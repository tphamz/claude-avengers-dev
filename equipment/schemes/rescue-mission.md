# Rescue Mission - Incident Response Scheme

## When to Equip

Use for bug fixes, incident response, and production issues. Optimized for
fast root-cause analysis and minimal blast radius.

## The Crew

| Phase        | Agent      | Equipment                     | Task                           |
| ------------ | ---------- | ----------------------------- | ------------------------------ |
| Triage       | BlackWidow | detective goggles             | Trace the bug, find root cause |
| Assessment   | Hulk       | deployment gadget             | Review the fix plan            |
| Surgery      | Thor       | project toolbelt              | Implement the fix              |
| Verification | Captain    | security lens (if applicable) | Review the fix                 |
| Confirmation | BlackWidow | detective goggles             | Verify fix and findings        |

## Phase 1: Triage

Dispatch BlackWidow with detective goggles.
Mission: trace data flow to root cause, assess blast radius, suggest fix approach.

## Phase 2: Assessment

Draft fix plan from BlackWidow's findings. Dispatch Hulk to review.
Present to user. For urgent issues, keep the plan concise.

## Phase 3: Surgery

Dispatch Thor to implement the minimal fix.
Write a regression test that reproduces the original bug.
Verify it fails without the fix and passes with it.

## Phase 4: Verification

Dispatch Captain to review.
Equip: security lens if the bug is security-related.

## Phase 5: Confirmation

Dispatch BlackWidow to verify Captain's findings.
If issues remain, loop max 3 cycles.

## Completion Criteria

- [ ] Root cause identified
- [ ] Fix implements targeting root cause
- [ ] Regression test added
- [ ] Full test suite passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS
- [ ] Code committed
