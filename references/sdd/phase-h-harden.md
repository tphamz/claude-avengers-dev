# SDD Phase H: Harden (stub)

Standard track. Mirrors `/bmad` Phase 4.5, over the OpenSpec change.

| Tool / procedure | Owner | Mode |
| ---------------- | ----- | ---- |
| `sdd-openspec.py validate <change>` | main loop | deterministic script |
| `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` (only when `_bmad/` exists) | main loop | wrapped skills (`/bmad` relay-config §3.12) |
| adversarial + edge-case review of the delta specs, proposal, design and tests.md | `Agent(avengers-dev:captain)`, `adversarial` lens | read-only subagent |
| applying fixes | main loop (Vision voice) | interactive |

## What happens

1. **Strict validation.** `validate` runs OpenSpec's `validate --strict` and also
   fails on the INFO issues that mean `archive` would refuse the change. Exit 1:
   its `blocking` issues are Criticals — fix them with the user before Captain runs.
2. **Captain** gets the change id and the `status` JSON (`change_dir_real`) and
   reviews every requirement and scenario: is it concrete, testable, and does it
   cover error and edge paths? Is every scenario mapped to a test in `tests.md`?
   Are the MODIFIED requirements copied whole? When `_bmad/` exists, the main loop
   first runs `bmad-review-adversarial-general` and `bmad-review-edge-case-hunter`
   over the change files (every wrapped skill runs in the main loop, `/bmad`
   relay-config §3.12) and passes their findings to Captain, who verifies them;
   otherwise the `adversarial` lens alone. Captain assigns
   `[CRITICAL]` / `[WARNING]` / `[SUGGESTION]`.
3. Captain reports only. Back in the main loop, walk the findings with the user,
   apply the agreed fixes to the change files, and re-run `validate`. Unresolved
   Criticals go to the gate, where passing needs `override` plus a reason
   (`/bmad` relay-config §3.11).

See `references/sdd/relay-config.md` for the phase map.
