---
name: sdd
description: >
  Initiate or resume a spec-driven (SDD) sequence in Vision's voice. quick and
  standard run on OpenSpec — a proposal and delta specs per change, merged into
  the living specs by a guarded archive — with Captain hardening and verifying,
  Hulk checking readiness, Thor building (tests first on standard), and IronMan
  holding the hard gate. full hands off to /bmad. Needs OpenSpec >= 1.13 installed
  separately.
allowed-tools: Skill, Agent, Bash, Read, Write
argument-hint: "[change-name] [quick|standard|full|resume]"
---

# SDD — Spec-Driven Development over OpenSpec (and BMAD)

This skill keeps the Avengers relay — crew, tracks, hard gate, KB lifecycle, md
workstation — and picks the spec engine by track: **OpenSpec** for `quick` and
`standard`, **BMAD** for `full` (handed to `/avengers-dev:bmad`). It does not
reimplement OpenSpec; it drives the `openspec` CLI through a guarded wrapper.

**IronMan's job here:** run the sequence, speak in Vision's voice at each phase
boundary, dispatch the owning Avenger for delegated phases, and hold the
design-implementation gate (standard track).

Scripts (every subcommand accepts `--project-dir`, default the current directory,
and prints `--help`):

- **sdd-openspec.py** — `${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py`,
  the only way the relay calls `openspec`. It sets `OPENSPEC_TELEMETRY=0` and
  `DO_NOT_TRACK=1` on every call.
- **workstation.py** — `${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py`
- **bmad-kb.py** — `${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py` (BMAD
  projects only)

Protocol, state schema and the directives (which reference `/bmad`'s by section
number): `${CLAUDE_PLUGIN_ROOT}/references/sdd/relay-config.md`. Per-phase stubs:
`${CLAUDE_PLUGIN_ROOT}/references/sdd/phase-*.md` and `track-quick.md`.

## Ownership Map — phase → tool → owner → tracks

| Phase | Tool / procedure | Owner | Tracks |
| ----- | ---------------- | ----- | ------ |
| 0 Preflight | `sdd-openspec.py preflight` → workstation → `init` → KB check (BMAD only) | main loop | quick, standard |
| E Explore (optional) | read `openspec/specs/` and the code with the user | main loop (Vision voice) | standard |
| P Propose | `sdd-openspec.py new` → `instructions` per artifact | main loop (Vision voice) | quick (lite), standard |
| H Harden | `sdd-openspec.py validate` + adversarial / edge-case review of the delta specs | `Agent(avengers-dev:captain)`, `adversarial` lens; fixes in main loop | standard |
| R Readiness | readiness of the change | `Agent(avengers-dev:hulk)` | standard |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** (standard) |
| B Build | tests first from `tests.md` (standard), then `tasks.md` | `Agent(avengers-dev:thor)` | quick, standard |
| V Verify + review | `references/sdd/verify.md` + code review; fix loop max 3 | `Agent(avengers-dev:captain)` | quick, standard |
| A Archive + KB | `sdd-openspec.py archive` → `bmad-kb.py impact` (BMAD only) → md commit | main loop | quick, standard |
| Full track | `Skill(avengers-dev:bmad)` with `<name> full` | `/bmad` | full |

## Tracks

| Track | Engine | Phases | Use when |
| ----- | ------ | ------ | -------- |
| `quick` | OpenSpec, `spec-driven` schema | 0 → P (lite) → B → V → A | small, well-understood change |
| `standard` | OpenSpec, `avengers-sdd` schema (tests artifact) | 0 → E (optional) → P → H → R → gate → B (tests first) → V → A | default for features |
| `full` | BMAD | handed to `/avengers-dev:bmad <name> full` | PRD, architecture, epics and ATDD are needed |

## Steps

> **Prompting:** every user-facing question here — the change name, the track, the
> resume choice, the md workstation questions, the phase confirmations, the gate,
> the incomplete-archive reason, and the md commit offers — is a **plain
> conversational question** in Vision's voice. Do **NOT** use a structured
> question/elicitation tool.

### 0. Preflight

Skip this step for the `full` track (Step 2 hands off first) and for a resume that
redirects to `/bmad`.

1. **OpenSpec and git.**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py preflight
   ```

   Exit 0: JSON `{openspec: {path, version, ok, min, pinned}, git: {version, ok},
   bmad, tea}` — keep `bmad`. If `openspec.version` differs from `pinned`, mention
   it once (the wrapper's guards were written against the pinned version). Exit 1:
   **STOP** — relay stderr (the install hint `npm i -g @fission-ai/openspec@latest`,
   or the git minimum) and exit. Never install OpenSpec.

2. **md workstation.** Follow `/avengers-dev:bmad` Step 0's workstation section
   (`/bmad` relay-config §3.13) with the `openspec` link:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py resolve --link openspec
   ```

   Exit 1: report the error and continue in-repo. Exit 0:
   - `ok` with every `symlinks` value `ok` or `in_repo` — nothing to ask
     (`symlinks.openspec: in_repo` means the user already chose to keep
     `openspec/` in the repo; never ask again).
   - `ok` otherwise — run `workstation.py set --path <path> --link openspec`
     (no question). Exit 0 wired; exit 2 already set. Exit 1 because `openspec/` is
     a non-empty directory or tracked in git: ask whether to move it into the
     workstation or keep it in the repo.
     - Move: run the migrate flow of `/avengers-dev:avengers-workstation` Step 3
       with `--link openspec` — preview with `--dry-run`, and for a tracked
       `openspec/` repeat its untrack warning plainly before any `--untrack`.
     - Keep in the repo: `workstation.py set --in-repo --link openspec`. It records
       `mdLinksInRepo: ["openspec"]` and leaves `mdWorkstation` and the `bmad` link
       alone. Exit 0 recorded; exit 2 already recorded.
   - `in_repo` — the whole project keeps its markdown in the repo, `openspec/`
     included; continue.
   - `guess`, `missing`, `broken` — run `/avengers-dev:avengers-workstation`
     Steps 1–4, passing `--link openspec` to every `set` and `migrate`.

   With a workstation, grant it as in `/avengers-dev:avengers-workstation` Step 4
   (`workstation.py grant-path`, then `manage-settings.py list-add … --dry-run` and
   write the printed JSON to `.claude/settings.local.json` with the Write tool;
   exit 2 already granted), so Captain and Hulk can read the change files. When
   `_bmad/` exists, also run `workstation.py check-config` as in `/bmad` Step 0.
   Record `md_workstation` (the path, or `null`) and `openspec_in_repo`: `true`
   when `openspec/` is not symlinked into the workstation — `md_workstation` is
   `null`, or `symlinks.openspec` is `in_repo`.

3. **OpenSpec init.**

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py init
   ```

   Exit 0: initialised (`openspec init --tools none`, the `avengers-sdd` schema,
   default schema set) — JSON lists the actions. Exit 2: already initialised,
   continue. Exit 1: relay stderr and stop; a dangling `openspec` symlink means
   re-running the workstation `set` above.

4. **KB check — only when `bmad` is true.** Run `bmad-kb.py status` and record its
   `head` as `kb_base_commit`. Report the `state`; a `missing` or `stale` KB is
   noted, not rebuilt — suggest `/bmad` if the change needs discovery. When `bmad`
   is false, say once that the KB is `openspec/specs/` alone and set
   `kb_base_commit: null`.

### 1. Parse Arguments

- **No argument**: ask for a change name (kebab-case, e.g. `add-user-export`), then
  the track.
- **`[change-name]`**: ask for the track, suggesting `standard`.
- **`[change-name] quick|standard|full`**: that track.
- **`[change-name] resume`** or **`resume [change-name]`**: resume.
- **`resume`** alone: list `.avengers/relay-sequences/sdd-*.yaml` and ask.

The change id is the name. `sdd-openspec.py new` refuses anything that is not
kebab-case (exit 1); ask again.

### 2. State, Resume, and the Full-Track Handoff

State lives at `.avengers/relay-sequences/sdd-{name}.yaml` (schema in
relay-config). If it exists, ask: "An SDD sequence named '{name}' already exists.
Resume it?"

- **Resume** follows `/bmad` relay-config §3.2: announce "Resuming SDD '{name}'
  ({track}) at Phase {phase}." and re-enter at `current_phase`, respecting
  `design_implementation_boundary_passed`. Refresh `md_workstation` and
  `openspec_in_repo` from Step 0.
- **`status: handed_off`** (full track): do not resume here. Say the sequence is
  owned by `/bmad`, and run `Skill(avengers-dev:bmad)` with `<name> resume`.

**New sequence:** write the state file with `status: active`, `track`,
`engine: openspec`, `change_id: <name>`, `current_phase: 0`,
`design_implementation_boundary_passed: false`, `gate_override: null`,
`archive_override: null`, `review_cycles: 0`, `md_workstation`, `openspec_in_repo`,
`kb_base_commit`.

**Full track:** write the state file with `status: handed_off`, `engine: bmad`,
`current_phase: 0`, then announce the handoff in Vision's voice and run
`Skill(avengers-dev:bmad)` with `<name> full`. `/sdd` stops conducting;
`/bmad` owns `bmad-{name}.yaml` from here.

### 3. Run the Phase Sequence (standard track)

Open every phase transition with the Vision identity header and a matching
catchphrase (`agents/vision.md`). Main-loop phases confirm the boundary with the
user before advancing (`/bmad` relay-config §3.5). Update `current_phase` at each
advance.

**Every delegation prompt** carries the change id, the track, and the current
`sdd-openspec.py status <change>` JSON (exit 0: `{change, schema, artifacts,
planning_complete, tasks_total, tasks_done, next, change_dir_real}`; exit 1:
report and stop). Subagents read and edit files under `change_dir_real`; they never
run `openspec` directly.

1. **E — Explore (optional).** Offer it. If accepted, read the relevant
   `openspec/specs/` capabilities and code with the user to settle scope. No
   artifact is written.
2. **P — Propose.** Run:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py new <change> --schema avengers-sdd
   ```

   Exit 0: JSON with `change_dir_real`. Exit 1: relay stderr (invalid name, or the
   change already exists — offer to resume it or pick another name). Then, while
   `status` reports a `next` artifact that is not `apply` or `archive`:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py instructions <artifact> <change>
   ```

   Exit 0: OpenSpec's JSON (`instruction`, `template`, `resolvedOutputPath`,
   `dependencies`). Draft the artifact with the user following `instruction` and
   `template`, and write it to `resolvedOutputPath` with the Write tool. Exit 1:
   relay stderr. Order: proposal → specs → design → tests → tasks. Every artifact
   the schema defines is written — OpenSpec only unlocks `tasks` once its
   dependencies exist. Details: `references/sdd/phase-p-propose.md`.

   **Loop guard:** after each write, run `status` again. If `next` names the same
   artifact as before the write, **stop the loop** — do not rewrite it again.
   Report the artifact, the path written, and the `status` JSON to the user (the
   file is usually at the wrong path or does not match the schema's `generates`
   pattern), fix it with the user, then resume.
3. **H — Harden.** Run `sdd-openspec.py validate <change>`. Exit 0: valid. Exit 1:
   the JSON `blocking` list (OpenSpec errors, strict warnings, and the "archive
   would refuse" INFO issues) are Criticals — fix them with the user and re-run.
   Then dispatch `Agent(avengers-dev:captain)` with the `adversarial` lens to
   review the change as in `references/sdd/phase-h-harden.md`; Captain assigns
   `[CRITICAL]`/`[WARNING]`/`[SUGGESTION]` and reports only. Walk the findings with
   the user, apply the agreed fixes, re-run `validate`. Record unresolved Criticals
   for the gate.
4. **R — Readiness.** Dispatch `Agent(avengers-dev:hulk)` to judge whether the
   change is ready to build: `planning_complete` is true; `validate` exits 0; every
   scenario maps to a test in `tests.md`; every test is owned by a task; tasks are
   ordered with the tests first in each group; `design.md` answers the open
   questions that would change the build. Hulk returns PASS or FAIL with reasons.
   **The gate reads the verdict Hulk returns.**
5. **Gate** — Step 4.
6. **B — Build.** Dispatch `Agent(avengers-dev:thor)` as in
   `references/sdd/phase-b-build.md`: the tests in `tests.md` first, run and seen
   to FAIL for the right reason, then `tasks.md` in order, ticking each task, then
   commit.
7. **V — Verify + review.** Dispatch `Agent(avengers-dev:captain)` with the commit
   range to run `references/sdd/verify.md` and his code review; one verdict. **Fix
   loop:** on FAIL, or CONDITIONAL PASS with any `[CRITICAL]`, Thor fixes (or the
   main loop edits a wrong spec with the user, then re-runs `validate`), then
   Captain re-reviews. Increment `review_cycles`; max 3, then escalate to the user.
   Advance only on PASS, or CONDITIONAL PASS with no `[CRITICAL]`.
8. **A — Archive + KB** — Step 5.

### 4. Design-Implementation Boundary — Hard Gate (R → B)

After Hulk's verdict, offer an **md commit** (Step 7, phase `design`). Then present
the verdict — plus any unresolved Harden Criticals — in Vision's voice and **stop**:

> Design-implementation boundary reached. The line must hold.
> **[1] Continue into implementation  [2] Exit** (artifacts saved, relay suspended)

This is `/bmad` relay-config §3.6 and §3.11, unchanged:

- **PASS and no unresolved Criticals** — [1] sets
  `design_implementation_boundary_passed: true` and proceeds to B.
- **FAIL, or unresolved Criticals** — [1] is accepted only when the user types
  `override` plus a reason; record `gate_override: {reason, at}`. A bare [1] is
  refused; restate the blockers.
- **[2]** sets `status: suspended` and stops.

No auto-advance, no batch-through.

### 5. Archive + KB (Phase A)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py archive <change>
```

Exit 0: JSON `{archived_as, path_real, specs_updated, totals, …}` — the delta specs
are merged into `openspec/specs/`. Report the totals. Exit 1: relay stderr. The
wrapper refuses when `tasks.md` has no tasks or any is incomplete, when `validate`
fails, and when OpenSpec's own JSON reports an error (its `code`, `message` and
`fix` are on stderr).

- **Incomplete tasks:** ask the user whether to finish them (back to B) or archive
  anyway. Only with an explicit reason, re-run with
  `--allow-incomplete --reason "<reason>"` and record `archive_override`.
- **Validation or OpenSpec refusal:** fix the delta specs with the user (back to P
  for spec edits), then retry.

Then:

1. **KB — only when `bmad` is true:** run `bmad-kb.py impact --base <kb_base_commit>`
   and follow `/avengers-dev:bmad` Step 5 (`references/bmad/phase-9-kb-refresh.md`):
   exit 2 no commits since base; `refresh_recommended` → confirm → refresh →
   `stamp`.
2. **Commit the specs.** These are independent; do both when both apply.
   - `openspec_in_repo: true` — dispatch `Agent(avengers-dev:thor)` to commit the
     `openspec/` changes in the code repo as `docs(openspec): archive <change>`
     (pathspec `openspec/`). This does not depend on `md_workstation`.
   - `md_workstation` set — offer the md commit (Step 7, phase `complete`) for the
     rest of the workstation.
3. Set `status: complete`.

### 6. Quick Track

`references/sdd/track-quick.md`. Step 0 as above, then:

1. **P (lite):** `new <change> --schema spec-driven`, then the `instructions` loop
   (with its loop guard) for a short proposal and specs, then `design.md`, then
   tasks. **Always write `design.md`:** `spec-driven`'s `tasks` requires `design`,
   so skipping it leaves `next` stuck on `design`. When the change needs no design,
   its body is one line, `Not needed: <reason>`. One confirmation at the end.
2. **B:** Thor works `tasks.md` (no tests-first step), commits.
3. **V:** Captain, `references/sdd/verify.md` + code review, fix loop max 3.
4. **A:** Step 5.

No Harden, Readiness or gate on this track.

### 7. md Commits (workstation only)

Offered at the gate (phase `design`) and after archive (phase `complete`). Skip
when `md_workstation` is `null`. Run `workstation.py md-status` and follow
`/avengers-dev:bmad` Step 8 exactly (exit 2 clean: say nothing; exit 1: note it;
exit 0: warn when `dedicated` is false, ask, and on yes Thor runs the pathspec
`git -C <toplevel> add` / `commit -m "docs(<repo_name>): <phase> artifacts"`).
Never push. An md commit never blocks the relay.

## Telemetry

OpenSpec sends anonymous usage telemetry by default. The wrapper sets
`OPENSPEC_TELEMETRY=0` and `DO_NOT_TRACK=1` on every call it makes. Outside the
relay, your own environment decides; leave those variables unset to allow it.
