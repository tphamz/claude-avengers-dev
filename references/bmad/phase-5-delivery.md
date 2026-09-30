# BMAD Phase 5: Readiness (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

This is the last design phase. After Phase 5, the relay either continues into
implementation (Phases 6-8) or pauses at the design-implementation boundary.

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
   NOT-READY.

## Design-Implementation Boundary (Hard Gate)

IronMan presents **both** results — the report status and Hulk's verdict — and
stops. If either is NOT READY / NOT-READY, recommend [2]; the user decides.
Require an explicit choice:

> [1] Continue into implementation  [2] Exit (artifacts saved, relay suspended)

Wait for the explicit user choice. Set `design_implementation_boundary_passed: true`
only on [1]. No auto-advance, no batch-through.

See `references/bmad/relay-config.md` §2.7 and §3.6 for the gate protocol.
