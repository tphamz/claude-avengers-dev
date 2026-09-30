# BMAD Phase 7: Build (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Iterative, per-story.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent |

## What happens

For each story in the sprint plan, Thor is dispatched to run `bmad-create-story`
(fill the story with implementation context) then `bmad-dev-story` (implement, write
tests, commit) autonomously, reporting back per story. After each report, the
main loop records the story's `baseline_commit` (story frontmatter) and the commit
SHA from Thor's report as `phase7_end_sha` in `loop_state.stories[<story_key>]`;
Phase 8 uses them to scope the story's review range.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
