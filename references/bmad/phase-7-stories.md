# BMAD Phase 7: Build (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Iterative, per-story.

| Real skill(s) | Owner | Mode | Tracks |
| ------------- | ----- | ---- | ------ |
| `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent | standard |
| `bmad-create-story` → `bmad-testarch-atdd` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent | full |

## What happens

For each story in the sprint plan, Thor is dispatched to run `bmad-create-story`
(fill the story with implementation context), then — **full track only** —
`bmad-testarch-atdd` (write failing acceptance tests from the story's ACs), then
`bmad-dev-story` (implement until the tests pass, commit), reporting back per story.

The full track requires the TEA module (`_bmad/tea/`), checked by
`bmad-kb.py preflight --track full` before the sequence starts.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
