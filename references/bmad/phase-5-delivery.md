# BMAD Phase 5: Readiness (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

This is the last design phase. After Phase 5, the relay either continues into
implementation (Phases 6-9) or pauses at the design-implementation boundary.

| Real skill | Owner | Mode |
| ---------- | ----- | ---- |
| `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | interactive + read-only verify |

## What happens

1. The main loop runs `bmad-check-implementation-readiness`, validating that PRD,
   architecture, and epics/stories are complete and coherent. It writes
   `{planning_artifacts}/implementation-readiness-report-{date}.md` step by step
   and ends with a status of READY / NEEDS WORK / NOT READY.
2. Resolve the newest report file from `_bmad/bmm/config.yaml` (relay-config
   `§2.8`) and dispatch Hulk read-only with that path and the planning artifacts
   it assessed. Hulk returns an independent verdict: READY / READY-WITH-CONCERNS /
   NOT-READY. **The gate reads both results**, not the report file alone.

## Design-Implementation Boundary (Hard Gate)

IronMan presents **both** results — the report status and Hulk's verdict — plus
any unresolved Phase 4.5 `[CRITICAL]` findings, and stops. If either result is
NOT READY / NOT-READY, recommend [2]. If either is NEEDS WORK /
READY-WITH-CONCERNS, flag it explicitly and list the cited gaps. In every case the
user decides. Require an explicit choice:

> [1] Continue into implementation  [2] Exit (artifacts saved, relay suspended)

- Neither result NOT READY / NOT-READY and no unresolved Criticals: [1] sets
  `design_implementation_boundary_passed: true`.
- Either result NOT READY / NOT-READY, or unresolved Criticals: [1] is accepted
  only when the user types `override` plus a reason. Record
  `gate_override: {reason, at}`. A bare [1] is refused.
- [2] sets `status: suspended`.

No auto-advance, no batch-through.

See `references/bmad/relay-config.md` §2.7 and §3.6 for the gate protocol and
§3.11 for the override.
