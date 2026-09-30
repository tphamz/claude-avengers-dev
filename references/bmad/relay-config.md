# BMAD Methodology Relay - Configuration

This is the configuration and protocol reference for the Avengers BMAD relay.
The relay **wraps the real BMAD-METHOD `bmad-*` skills** — it does not reimplement
them. Vision (the conductor) reads this at relay start to understand operational
parameters and the phase→skill+owner map.

## Relay Identity

- **Name:** BMAD — the Avengers relay that conducts the real BMAD-METHOD framework
  (mnemonic: *Build More Architect Dreams*). It orchestrates the installed `bmad-*`
  skills through the crew; it is not a competing methodology.
- **Type:** skill-wrapping, spec-driven methodology-relay
- **Phases:** 0 KB check, design 1a-5 (with 4.5 Spec Hardening), implementation
  6-8, 9 KB Refresh
- **Tracks:** `quick` | `standard` (default) | `full`
- **Conductor:** Vision agent (voice + map, not executor)

## Phase Map — phase → real skill → owner → tracks

Each phase either invokes its real `bmad-*` skill **in the main loop** (interactive
skills — Vision's voice, so the skill can elicit from the user) or **dispatches the
owning Avenger** to run the real skill autonomously (non-interactive phases).

| Phase | Real skill(s) | Owner | Tracks |
|-------|---------------|-------|--------|
| 0 KB check | `bmad-kb.py status` | main loop | all |
| 1a Discovery (conditional) | `bmad-document-project` + `bmad-generate-project-context`, then `bmad-kb.py stamp` | main loop (Vision voice) | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` create; optional validate / `bmad-advanced-elicitation` | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | `Agent(avengers-dev:captain)`, `adversarial` lens | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | standard, full |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full only) → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full only) + `bmad-retrospective` | `Agent(avengers-dev:captain)` | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → `bmad-document-project` + `bmad-generate-project-context` → `stamp` | main loop (Vision voice) | all |
| Quick track | `bmad-quick-dev`, then Captain reviews the diff | main loop, then `Agent(avengers-dev:captain)` | quick |

Per-phase stubs: `phase-0-kb.md`, `phase-1-assessment.md` … `phase-8-review.md`,
`phase-4.5-hardening.md`, `phase-9-kb-refresh.md`, and `track-quick.md`.

**Why the split:** the wrapped `bmad-*` skills are interactive. A subagent runs
blind and cannot elicit, so every interactive skill runs in the main loop (§3.10);
only the non-interactive phases (whose real work belongs to a specialist Avenger
anyway) are delegated.

<!-- SEAM: Phases 1a–4 could later be flipped to a fully-autonomous Vision subagent
     if the wrapped bmad-* skills gain a batch / non-interactive mode. Until then
     they must stay in the main loop because they ask the user questions. -->

## State File

Location: `.avengers/relay-sequences/bmad-{name}.yaml`

### State Schema

```yaml
sequence_id: string           # Unique identifier: bmad-{name}
name: string                  # Human name: {name}
status: enum                  # active | suspended | complete | closed | abandoned
track: enum                   # quick | standard | full   (missing -> standard)
current_phase: string         # 0 | 1a | 1b | 2 | 3 | 4 | 4.5 | 5 | 6 | 7 | 8 | 9
                              # (quick track: 0 | quick-dev | review | 9)
                              # new sequences start at 0
design_implementation_boundary_passed: bool  # Phase 5->6 hard gate
gate_override:                # null, or set when the gate is passed despite blockers
  reason: string              #   user-supplied reason (required)
  at: timestamp
kb_status_at_start: enum      # missing | unstamped | fresh | stale | unknown (Phase 0)
kb_base_commit: string | null # HEAD at Phase 0; base for Phase 9 impact
md_workstation: string | null # md workstation path from Step 0 (§3.11); null = in-repo
created_at: timestamp
last_active: timestamp

relay_modifiers:
  existing_code_in_scope: bool   # Brownfield mode (drives Phase 1a skill choice)

loop_state:                      # Phase 7 only
  total_items: int
  completed: list
  in_progress: string | null
  remaining: list
```

Artifact paths are owned by the wrapped `bmad-*` skills (BMAD-METHOD writes under
its configured `output_folder` and `project_knowledge`) — the relay does not
dictate them. With an md workstation, `output_folder` is a symlink into it (§3.11).

## Protocol Directives

### §2.2 Close-Out Dialogue

When user says 'stop' during any phase:
1. Save current state to disk
2. Ask: "Save and suspend (resume later) or close out permanently?"
3. `suspended` = paused, resume available
4. `closed` = user is done; artifacts preserved but relay inactive

### §2.5 No Role-Play

Operate as Vision's functional persona — do not role-play as human characters.
The wrapped `bmad-*` skills bring their own domain personas; the relay narration
stays in Vision's voice.

### §2.7 Deterministic-First

Readiness (Phase 5) is delegated to `bmad-check-implementation-readiness`, which
maximizes deterministic checks. Trust the skill's verdict; surface LLM judgment as
advisory, not blocking.

### §3.2 Resume Protocol

On resume, read the state file first. Surface to user:
> "Resuming BMAD '{name}' at Phase {N}: {phase-name} ({context})."

Re-enter at `current_phase`, respecting `design_implementation_boundary_passed`.

**Resume defaults.** A **legacy state file** is one with **no `track` key**
(written before tracks and Phases 0/4.5/9 existed). For legacy files only:

- `track` → `standard`.
- At `8` or `complete` → finish as before; **not** routed into Phase 9.
- Otherwise → continue through Phase 9. With no `kb_base_commit`, Phase 9 uses the
  `stamped_commit` reported by `bmad-kb.py status`; if there is none, Phase 9 is
  skipped with a note.
- Missing `gate_override` → `null`.

State files with a `track` key follow the normal flow, including Phase 9.

### §3.5 Phase Boundary Confirmation

Each interactive phase announces completion and waits for user confirmation before
advancing. Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"
Delegated phases report through their Avenger; IronMan relays, then advances.

### §3.6 Design-Implementation Boundary (Hard Gate)

The boundary between Phase 5 and Phase 6 is a hard gate. User must explicitly choose:
- [1] Continue into implementation
- [2] Exit (artifacts saved, relay suspended)

No auto-advance. No batch-through. Set `design_implementation_boundary_passed: true`
only on [1]. The gate reads the readiness verdict **Hulk returns**, not a file. If
that verdict is FAIL, or Phase 4.5 left `[CRITICAL]` findings unresolved, [1]
requires an override (§3.9).

### §3.7 Scope Creep Prevention

During Phase 7, if implementation surfaces out-of-scope requirements:
- Surface to user with three options (note/defer, pause-replan, add-informally)
- Do not implement out-of-scope items silently

### §3.8 KB Lifecycle

The knowledge base (KB) is two files produced by the real BMAD skills, at paths
read from `_bmad/bmm/config.yaml` (falling back to `_bmad/core/config.yaml`, then
defaults `docs` / `_bmad-output`):

- `{project_knowledge}/index.md` — `bmad-document-project`
  (`initial_scan` | `full_rescan` | `deep_dive`)
- `{output_folder}/project-context.md` — `bmad-generate-project-context`

The freshness marker is `<workstation>/avengers/kb.json` with an md workstation,
else `.avengers/kb.json`; reads fall back to the legacy `.avengers/kb.json` and
`stamp` moves it into the workstation. Schema:
`{version: 2, index_path, context_path, branches: {<branch>: {commit, stamped_at,
arch_hashes}}}` — keyed per branch so worktrees on different branches do not
overwrite each other (detached HEAD uses `HEAD@<sha7>`). A branch with no entry
falls back to the newest entry and reports `stale` with a `branch_unstamped`
signal. Paths are relative to the workstation (in-repo paths as
`{project-root}/...`). Read the marker through `bmad-kb.py status`, not by path.

- **Build only when missing** — Phase 0 `status` = `missing` → Phase 1a.
- **Offer refresh when meaningfully stale** — `stale` means at least one impact
  signal since the stamp (breaking-change commit, architecture doc under the output
  folder, dependency manifest, migration, API contract, new top-level dir) or 20+
  changed files outside the KB dirs, `output_folder`, `.avengers/`, and `_bmad/`.
  An `unknown_stamp` signal (the stamped commit is no longer in history, e.g.
  rebased away) also makes the KB `stale`. When the output folder is outside git
  (an md workstation), architecture docs are compared by the sha256 hashes stored
  at stamp time instead of by git diff. The user decides.
- **Not a git repo** — `status` reports `unknown` (or `unstamped` with a null
  `head`); `stamp` and `impact` exit 1, so they are skipped and freshness is not
  tracked.
- **Refresh at the end when the change is important or breaking** — Phase 9 runs
  `impact --base <kb_base_commit>`; if `refresh_recommended`, the user confirms,
  then `deep_dive` per area (3 or fewer `changed_areas`) or `full_rescan`, then
  `bmad-generate-project-context`, then `stamp`.

### §3.9 Gate Override

When readiness is FAIL, or Phase 4.5 `[CRITICAL]` findings are unresolved, a bare
[1] at the gate is refused. The user must type `override` plus a reason. Record
`gate_override: {reason, at}` in the state file and set
`design_implementation_boundary_passed: true`.

### §3.10 Interactive Skills Run in the Main Loop

Any wrapped skill that asks the user questions — including `bmad-document-project`
and `bmad-generate-project-context` in Phases 1a and 9, and `bmad-quick-dev` on the
quick track — runs in the main loop via `Skill(bmad-X)`. Subagents are dispatched
only for skills that need no user input (4.5, 5, 7, 8).

### §3.11 md Workstation and md Commits

**Step 0 (every run):** after preflight, `workstation.py resolve`. `ok` continues
(a missing or mismatched symlink is repaired with `set`); `in_repo` continues
in-repo; `guess` / `missing` / `broken` run the `/avengers-workstation` flow, where
the user may still choose in-repo. Then `workstation.py check-config` (exit 1 — `_bmad/`
missing or `output_folder` outside the project — is reported and skipped): keys
outside `output_folder` are offered for an opt-in, per-key `repoint-config` (it edits the
team's committed config — say so). Declined keys are recorded in
`.avengers/settings.json` → `mdRepointDeclined` and not offered again. It runs on
every run because a BMAD reinstall can undo a re-point and a symlink can dangle.
Record `md_workstation` in the state file.

**md commits:** offered after the Phase 1a stamp, at the hard gate, and at
completion (end of Phase 9, any track), only when `md_workstation` is set.
The workstation folder is `<md-root>/<repo-name>-mds/`.

1. `workstation.py md-status` — exit 2 (clean, or not a git repo): skip silently.
2. Exit 0: if `dedicated` is false (the md repo is `$HOME` or contains the project),
   warn first that the commit lands in that repo. Then ask "Commit N md changes in
   <md repo>?"
3. On yes, Thor runs `git -C <toplevel> add -- <rel>`, then
   `git -C <toplevel> commit -m "docs(<repo-name>): <phase> artifacts" -- <rel>`.
   The pathspec commit leaves anything else staged in the md repo untouched.
4. A hook or signing failure is reported and the relay continues. Never push.

**Known limitation:** `bmad-story-automator` rejects artifact paths that resolve
outside the repo root, so it does not work with a workstation. The relay's Phase 7
(Thor running `bmad-create-story` → `bmad-dev-story`) does not use it.

## Execution Model — wrap, don't reimplement

Each phase **invokes its real `bmad-*` skill** (main loop) or **dispatches its
owner** (subagent). There are no persona overlays to load and no self-contained
phase logic — the wrapped skill carries the authoring instructions. The
`references/bmad/phase-{N}-*.md` and `track-quick.md` files are thin stubs
documenting the mapping (skill + owner + mode) plus the wrapped skill's completion
criteria, for quick lookup at phase entry.
