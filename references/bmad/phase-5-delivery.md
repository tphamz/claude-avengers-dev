# BMAD Phase 5: Readiness (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

This is the last design phase. After Phase 5, the relay either continues into
implementation (Phases 6-9) or pauses at the design-implementation boundary.

| Real skill | Owner | Mode |
| ---------- | ----- | ---- |
| `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | autonomous subagent |

## What happens

Hulk is dispatched to run `bmad-check-implementation-readiness` autonomously —
validating that PRD, architecture, and epics/stories are complete and coherent —
and returns a PASS/FAIL readiness verdict with reasons. **The gate reads the
verdict Hulk returns**, not a file on disk.

## Design-Implementation Boundary (Hard Gate)

IronMan presents Hulk's readiness verdict, plus any unresolved Phase 4.5
`[CRITICAL]` findings, and stops. Require an explicit choice:

> [1] Continue into implementation  [2] Exit (artifacts saved, relay suspended)

- Readiness PASS and no unresolved Criticals: [1] sets
  `design_implementation_boundary_passed: true`.
- Readiness FAIL, or unresolved Criticals: [1] is accepted only when the user
  types `override` plus a reason. Record `gate_override: {reason, at}`. A bare [1]
  is refused.
- [2] sets `status: suspended`.

No auto-advance, no batch-through.

See `references/bmad/relay-config.md` §3.6 for the gate protocol and §3.9 for the
override.
