# BMAD Phase 5: Readiness (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

This is the last design phase. After Phase 5, the relay either continues into
implementation (Phases 6-8) or pauses at the design-implementation boundary.

| Real skill | Owner | Mode |
| ---------- | ----- | ---- |
| `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | autonomous subagent |

## What happens

Hulk is dispatched to run `bmad-check-implementation-readiness` autonomously —
validating that PRD, architecture, and epics/stories are complete and coherent —
and reports the readiness verdict.

## Design-Implementation Boundary (Hard Gate)

IronMan presents Hulk's readiness result and stops. Require an explicit choice:

> [1] Continue into implementation  [2] Exit (artifacts saved, relay suspended)

Wait for the explicit user choice. Set `design_implementation_boundary_passed: true`
only on [1]. No auto-advance, no batch-through.

See `references/bmad/relay-config.md` §3.6 for the gate protocol.
