# SDD Phase V: Verify + Review (stub)

Quick and standard tracks.

| Procedure | Owner | Mode |
| --------- | ----- | ---- |
| `references/sdd/verify.md` + code review of Thor's diff | `Agent(avengers-dev:captain)` | autonomous subagent |
| fixes | `Agent(avengers-dev:thor)` (or main loop when a spec must change) | as needed |

## What happens

1. Captain gets the change id, the track, the `status` JSON and the commit range.
   He runs the verify procedure (Completeness, Correctness, Coherence against the
   delta specs; on the standard track, every scenario has a passing test) and his
   normal code review, and returns one verdict.
2. **Fix loop:** on FAIL, or CONDITIONAL PASS with any `[CRITICAL]`, Thor fixes the
   flagged items — or, when a spec is wrong rather than the code, the main loop
   edits the delta spec with the user and re-runs `validate` — then Captain
   re-reviews. Max 3 cycles (`review_cycles`), then escalate to the user.
3. Advance to Archive only on PASS, or CONDITIONAL PASS with no `[CRITICAL]`.

See `references/sdd/relay-config.md` for the phase map.
