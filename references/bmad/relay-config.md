# BMAD Methodology Relay - Configuration

This is the configuration and protocol reference for the Avengers BMAD relay.
The relay **wraps the real BMAD-METHOD `bmad-*` skills** — it does not reimplement
them. Vision (the conductor) reads this at relay start to understand operational
parameters and the phase→skill+owner map.

## Relay Identity

- **Name:** BMAD — the Avengers relay that conducts the real BMAD-METHOD framework
  (mnemonic: *Build More Architect Dreams*). It orchestrates the installed `bmad-*`
  skills through the crew; it is not a competing methodology.
- **Type:** skill-wrapping methodology-relay
- **Phases:** 8 (design 1-5, implementation 6-8)
- **Conductor:** Vision agent (voice + map, not executor)

## Phase Map — phase → real skill → owner → mode

Every phase except Phase 7 invokes its real `bmad-*` skill **in the main loop**
(Vision's voice), so the skill can elicit from the user and write its artifacts.
In Phases 1a, 5 and 8 the owning Avenger is then dispatched **read-only to verify**
the result. Phase 7 dispatches Thor to build.

| Phase | Real skill(s) | Owner | Mode |
|-------|---------------|-------|------|
| 1a Discovery | `bmad-document-project` / `bmad-investigate` | main loop; `Agent(avengers-dev:blackwidow)` verifies | interactive + verify |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |
| 2 PRD | `bmad-prd` | main loop (Vision voice) | interactive |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | interactive + verify |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | light |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | interactive + verify |

**Why the split:** the wrapped `bmad-*` skills halt for user input and write
artifacts step by step; `bmad-code-review` also spawns its own subagents. A
subagent runs blind and cannot elicit, and BlackWidow, Hulk and Captain have no
Write, Edit or Agent tools. So the skills run in the main loop and those owners
verify the output read-only. The main loop may read broadly and write BMAD
artifacts while running a wrapped skill, but never modifies source code — code
changes (including code-review patches) always go to Thor.

<!-- SEAM: A main-loop phase could later move to a write-capable subagent if its
     wrapped skill gains a batch mode. Never move one to a read-only agent, and
     never while the skill still asks the user questions. -->

## State File

Location: `.avengers/relay-sequences/bmad-{name}.yaml`

### State Schema

```yaml
sequence_id: string           # Unique identifier: bmad-{name}
name: string                  # Human name: {name}
status: enum                  # active | suspended | complete | closed | abandoned
current_phase: string         # 1a | 1b | 2 | 3 | 4 | 5 | 6 | 7 | 8
design_implementation_boundary_passed: bool  # Phase 5->6 hard gate
created_at: timestamp
last_active: timestamp

relay_modifiers:
  existing_code_in_scope: bool   # Brownfield mode (drives Phase 1a skill choice)

loop_state:                      # Phases 7 and 8
  total_items: int
  completed: list
  in_progress: string | null
  remaining: list
  stories:                       # per story key (story file name without .md)
    <story_key>:
      baseline_commit: string    # from story frontmatter (or NO_VCS)
      phase7_end_sha: string     # commit SHA from Thor's Phase 7 report
      phase8_fix_shas: list      # commit SHA from each Phase 8 Thor fix
      review_cycles: int         # Phase 8 Thor → Captain → BlackWidow cycles (max 3)
```

Artifact paths are owned by the wrapped `bmad-*` skills and resolved from
`_bmad/bmm/config.yaml` (see `§2.8`) — the relay does not dictate them.

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

Readiness (Phase 5) runs `bmad-check-implementation-readiness` in the main loop;
its report carries a status of READY / NEEDS WORK / NOT READY. Hulk then gives an
independent verdict (READY / READY-WITH-CONCERNS / NOT-READY) on that report. The
gate shows **both**. If either is NOT READY / NOT-READY, IronMan recommends [2]
Exit. If either is NEEDS WORK / READY-WITH-CONCERNS, IronMan flags it explicitly
and lists the cited gaps. In every case the user decides. Neither verdict
auto-advances or auto-blocks the gate.

### §2.8 Artifact Path Resolution

Before dispatching a verifying Avenger, the main loop reads
`_bmad/bmm/config.yaml`, substitutes `{project-root}`, and passes **concrete file
paths** — never globs or unresolved `{placeholders}`. Keys and installer defaults:

| Key | Default | Written there |
|-----|---------|---------------|
| `project_knowledge` | `docs` | `bmad-document-project` output |
| `planning_artifacts` | `_bmad-output/planning-artifacts` | `implementation-readiness-report-{date}.md` (pass the newest file) |
| `implementation_artifacts` | `_bmad-output/implementation-artifacts` | story files, `sprint-status.yaml`, `deferred-work.md`, `investigations/{slug}-investigation.md`, `epic-{N}-retro-{date}.md` |

Phase 8 also needs, per story: the story file path, its `loop_state.stories`
entry (the review range is `<baseline_commit>..<phase7_end_sha>` plus each Phase 8
fix commit; never `..HEAD`, which includes later stories), and its story key (the
story file name without `.md`, e.g. `1-2-user-auth`) for the close-out write to
`sprint-status.yaml`. See `references/bmad/phase-8-review.md`.

### §3.2 Resume Protocol

On resume, read the state file first. Surface to user:
> "Resuming BMAD '{name}' at Phase {N}: {phase-name} ({context})."

Re-enter at `current_phase`, respecting `design_implementation_boundary_passed`.

### §3.5 Phase Boundary Confirmation

Each interactive phase announces completion and waits for user confirmation before
advancing. Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"
Phases with a verifying Avenger (1a, 5, 8) and the Phase 7 build report through
that Avenger; IronMan relays, then advances.

### §3.6 Design-Implementation Boundary (Hard Gate)

The boundary between Phase 5 and Phase 6 is a hard gate. User must explicitly choose:
- [1] Continue into implementation
- [2] Exit (artifacts saved, relay suspended)

No auto-advance. No batch-through. Set `design_implementation_boundary_passed: true`
only on [1].

### §3.7 Scope Creep Prevention

During Phase 7, if implementation surfaces out-of-scope requirements:
- Surface to user with three options (note/defer, pause-replan, add-informally)
- Do not implement out-of-scope items silently

## Execution Model — wrap, don't reimplement

Each phase **invokes its real `bmad-*` skill** (main loop, then a read-only owner
verifies where one is mapped) or, in Phase 7, **dispatches Thor** to build. There are no persona overlays to load and no self-contained
phase logic — the wrapped skill carries the authoring instructions. The
`references/bmad/phase-{N}-*.md` files are thin stubs documenting the mapping
(skill + owner + mode) plus the wrapped skill's completion criteria, for quick
lookup at phase entry.
