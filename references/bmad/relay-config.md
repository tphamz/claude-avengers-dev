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

Each phase either invokes its real `bmad-*` skill **in the main loop** (interactive
phases — Vision's voice, so the skill can elicit from the user) or **dispatches the
owning Avenger** to run the real skill autonomously (non-interactive phases).

| Phase | Real skill(s) | Owner | Mode |
|-------|---------------|-------|------|
| 1a Discovery | `bmad-document-project` / `bmad-investigate` | `Agent(avengers-dev:blackwidow)` | autonomous |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |
| 2 PRD | `bmad-prd` | main loop (Vision voice) | interactive |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | autonomous |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | light |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | `Agent(avengers-dev:captain)` | autonomous |

**Why the split:** the wrapped `bmad-*` skills are interactive. A subagent runs
blind and cannot elicit, so every interactive phase runs in the main loop; only the
non-interactive phases (whose real work belongs to a specialist Avenger anyway) are
delegated.

<!-- SEAM: Phases 1b–4 could later be flipped to a fully-autonomous Vision subagent
     if the wrapped bmad-* skills gain a batch / non-interactive mode. Until then
     they must stay in the main loop because they ask the user questions. -->

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

loop_state:                      # Phase 7 only
  total_items: int
  completed: list
  in_progress: string | null
  remaining: list
```

Artifact paths are owned by the wrapped `bmad-*` skills (BMAD-METHOD writes under
`docs/` by its own conventions) — the relay does not dictate them.

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

### §3.5 Phase Boundary Confirmation

Each interactive phase announces completion and waits for user confirmation before
advancing. Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"
Delegated phases report through their Avenger; IronMan relays, then advances.

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

Each phase **invokes its real `bmad-*` skill** (main loop) or **dispatches its
owner** (subagent). There are no persona overlays to load and no self-contained
phase logic — the wrapped skill carries the authoring instructions. The
`references/bmad/phase-{N}-*.md` files are thin stubs documenting the mapping
(skill + owner + mode) plus the wrapped skill's completion criteria, for quick
lookup at phase entry.
