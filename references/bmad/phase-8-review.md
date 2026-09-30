# BMAD Phase 8: Review (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Last implementation phase; advances to Phase 9 (KB Refresh).

| Real skill(s) | Owner | Mode | Tracks |
| ------------- | ----- | ---- | ------ |
| `bmad-code-review` + `bmad-retrospective` | `Agent(avengers-dev:captain)` | autonomous subagent | standard |
| `bmad-code-review` + `bmad-testarch-trace` + `bmad-retrospective` | `Agent(avengers-dev:captain)` | autonomous subagent | full |

## What happens

Captain is dispatched to run `bmad-code-review` on the sprint's changes, then —
**full track only** — `bmad-testarch-trace` to map every acceptance criterion to a
test, and `bmad-retrospective` at sprint end, and reports the verdict.

- On FAIL/CONDITIONAL, or a trace FAIL, the flagged stories loop back through Thor
  (Phase 7), max 3 cycles, then escalate to the user.
- On a clean verdict, announce sprint completion and advance to **Phase 9**. Phase
  8 no longer sets `complete`; Phase 9 does.

Authoring instructions and completion criteria are owned by the skills. See
`references/bmad/relay-config.md` for the full phase map.
