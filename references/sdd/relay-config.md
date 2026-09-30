# SDD Relay - Configuration

This is the configuration and protocol reference for `/sdd`, the Avengers
spec-driven relay. It keeps the Avengers structure — the crew, tracks, the hard
gate, the KB lifecycle and the md workstation — and changes the spec engine per
track:

- `quick` and `standard` run on **OpenSpec** (a proposal and delta specs per change;
  `archive` merges them into the living specs under `openspec/specs/`).
- `full` hands off to **BMAD** (`/bmad <name> full`), for PRD, architecture, epics
  and test-first work.

Vision conducts both engines. The `/bmad` protocol directives in
`${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md` apply here **by section
number**; this file only records what differs.

## Relay Identity

- **Name:** SDD — the Avengers spec-driven relay over OpenSpec (quick, standard) and
  BMAD (full)
- **Type:** tool-wrapping, spec-driven methodology relay
- **Engine:** OpenSpec >= 1.13 (tested with 1.13.2), a separate install
  (`npm i -g @fission-ai/openspec@latest`); Avengers never installs it
- **Wrapper:** `${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py` — the only
  way the relay calls `openspec`
- **Tracks:** `quick` | `standard` (default) | `full`
- **Conductor:** Vision agent (voice + map, not executor)

## Phase Map — phase → tool → owner → tracks

| Phase | Tool / procedure | Owner | Tracks |
|-------|------------------|-------|--------|
| 0 Preflight | `sdd-openspec.py preflight` → workstation (`--link openspec`) → `sdd-openspec.py init` → KB check (BMAD only) | main loop | quick, standard |
| E Explore (optional) | read `openspec/specs/` and the code with the user | main loop (Vision voice) | standard |
| P Propose | `sdd-openspec.py new` → `instructions <artifact>` per artifact | main loop (Vision voice) | quick (lite), standard |
| H Harden | `sdd-openspec.py validate`, then adversarial + edge-case review of the delta specs | `Agent(avengers-dev:captain)`, `adversarial` lens; fixes in main loop | standard |
| R Readiness | readiness check of the change | `Agent(avengers-dev:hulk)` | standard |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** (standard) |
| B Build | quick: tasks.md; standard: failing tests from tests.md first, then tasks.md | `Agent(avengers-dev:thor)` | quick, standard |
| V Verify + review | `references/sdd/verify.md` + code review; fix loop, max 3 | `Agent(avengers-dev:captain)` | quick, standard |
| A Archive + KB | `sdd-openspec.py archive` → `bmad-kb.py impact` (BMAD only) → md commit | main loop | quick, standard |
| Full track | `Skill(avengers-dev:bmad)` with `<name> full` | `/bmad` | full |

Per-phase stubs: `phase-0-preflight.md`, `phase-p-propose.md`, `phase-h-harden.md`,
`phase-b-build.md`, `phase-v-verify.md`, `phase-a-archive.md`, and `track-quick.md`.

**Why the split:** the same as `/bmad` §3.10. Propose, Explore, applying hardening
fixes and the gate ask the user questions, so they run in the main loop. Harden,
Readiness, Build and Verify need no user input and belong to a specialist Avenger.

## Schemas

Each change pins its schema in its `.openspec.yaml`, because `new` always passes
`--schema`:

- `quick` → `spec-driven` (OpenSpec's built-in: proposal → specs → design → tasks)
- `standard` → `avengers-sdd` (forked from `spec-driven`, with a `tests` artifact
  between specs/design and tasks: one failing test per WHEN/THEN scenario)

`sdd-openspec.py init` copies `avengers-sdd` into `openspec/schemas/` and makes it
the default in a new `openspec/config.yaml`. It is never named `spec-driven`: that
would shadow the built-in schema and turn off OpenSpec's task-numbering check.

## State File

Location: `.avengers/relay-sequences/sdd-{name}.yaml`

```yaml
sequence_id: string           # sdd-{name}
name: string                  # {name}
status: enum                  # active | suspended | complete | closed | abandoned | handed_off
track: enum                   # quick | standard | full
engine: enum                  # openspec | bmad (full track: bmad, status handed_off)
change_id: string | null      # OpenSpec change id (kebab-case; defaults to {name})
current_phase: string         # 0 | E | P | H | R | gate | B | V | A
design_implementation_boundary_passed: bool  # standard track gate (quick: n/a)
gate_override:                # null, or set when the gate is passed despite blockers
  reason: string
  at: timestamp
md_workstation: string | null # workstation path from Step 0; null = in-repo
openspec_in_repo: bool        # openspec/ not symlinked into the workstation
                              # (md_workstation null, or mdLinksInRepo has openspec);
                              # archive then commits openspec/ in the code repo
kb_base_commit: string | null # HEAD at Step 0 (BMAD projects only); base for impact
review_cycles: int            # Verify + review cycles used (max 3)
archive_override:             # null, or set when archive ran with --allow-incomplete
  reason: string
  at: timestamp
created_at: timestamp
last_active: timestamp
```

**Full-track handoff.** `/sdd <name> full` writes `status: handed_off`,
`engine: bmad`, `current_phase: 0`, then runs `Skill(avengers-dev:bmad)` with
`<name> full`. From then on `/bmad` owns the state in `bmad-{name}.yaml`. A later
`/sdd <name> resume` on a `handed_off` file redirects to `/bmad <name> resume`.
`sdd-x` and `bmad-x` files coexist: `/bmad` only reads `bmad-*` files.

## Protocol Directives

The `/bmad` directives apply unchanged unless noted. Section numbers refer to
`references/bmad/relay-config.md`.

| `/bmad` directive | In `/sdd` |
|-------------------|-----------|
| §2.2 Close-Out Dialogue | unchanged |
| §2.5 No Role-Play | unchanged; narration stays in Vision's voice |
| §2.7 Deterministic-First | the deterministic check is `sdd-openspec.py validate` (strict, archive refusals included). Hulk's readiness and Captain's verify judgment are advisory on top of it |
| §3.2 Resume Protocol | unchanged, read against `sdd-{name}.yaml`; a `handed_off` file redirects to `/bmad` |
| §3.5 Phase Boundary Confirmation | applies at every main-loop phase and at the gate |
| §3.6 Design-Implementation Boundary | the gate sits between R (Readiness) and B (Build) on the standard track; the quick track has none |
| §3.7 Scope Creep Prevention | applies in B; an out-of-scope requirement becomes a new change, a spec edit (back to P), or an informal note |
| §3.8 KB Lifecycle | only when `_bmad/` exists. Without BMAD the KB is `openspec/specs/` alone, refreshed by `archive` |
| §3.9 Gate Override | unchanged: readiness FAIL or unresolved Harden `[CRITICAL]`s need `override` plus a reason |
| §3.10 Interactive Skills Run in the Main Loop | unchanged; delegated phases are H, R, B and V |
| §3.11 md Workstation and md Commits | Step 0 adds the `openspec` link; md commits are offered at the gate (`design`) and after archive (`complete`) |

### SDD-specific directives

1. **The wrapper is the only OpenSpec caller.** Every `openspec` call goes through
   `sdd-openspec.py`, which sets `OPENSPEC_TELEMETRY=0` and `DO_NOT_TRACK=1` and runs
   from the real parent of a symlinked `openspec/`. Subagents read and edit the
   change files directly under `change_dir_real`; they do not run `openspec`.
2. **No `/opsx` commands.** `init` uses `--tools none`, so no `/opsx:*` commands or
   `openspec-*` skills are installed and nothing bypasses the relay. The upstream
   `/opsx:archive` skill merges specs through the model; the relay uses the CLI.
3. **Subagent inputs.** Every delegation prompt carries the change id and the
   `sdd-openspec.py status` JSON (`change_dir_real`, `artifacts`, `tasks_*`), so no
   subagent has to pick between changes. Step 0 grants the workstation path
   (`workstation.py grant-path`), so Captain and Hulk read it without prompts.
4. **Archive is guarded.** `sdd-openspec.py archive` refuses missing or incomplete
   tasks unless the user confirms a reason (`--allow-incomplete --reason`, recorded
   as `archive_override`), validates first, and reads OpenSpec's JSON result.
5. **OpenSpec Stores are not used.** They share one flat change namespace across
   repos and ignore the `store:` pointer when local content exists. The md
   workstation gives each repo its own `openspec/` instead.

## Telemetry

OpenSpec sends anonymous usage telemetry by default. The wrapper opts out on every
call it makes (`OPENSPEC_TELEMETRY=0`, `DO_NOT_TRACK=1`). Running `openspec`
yourself outside the relay follows your own environment; to allow telemetry there,
leave those variables unset.
