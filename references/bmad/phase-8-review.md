# BMAD Phase 8: Review & Completion (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Final phase.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-code-review` + `bmad-retrospective` | `Agent(avengers-dev:captain)` | autonomous subagent |

## What happens

Captain is dispatched to run `bmad-code-review` on the sprint's changes (and
`bmad-retrospective` at sprint end) autonomously, and reports the verdict. On
FAIL/CONDITIONAL, the flagged stories loop back through Thor (Phase 7), max 3 cycles,
then escalate to the user.

On a clean verdict, announce sprint completion and transition the sequence to
`complete` in the state file.

Authoring instructions and completion criteria are owned by the skills. See
`references/bmad/relay-config.md` for the full phase map.
