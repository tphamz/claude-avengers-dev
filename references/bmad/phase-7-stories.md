# BMAD Phase 7: Build (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Iterative, per-story.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent |

## What happens

For each story in the sprint plan, Thor is dispatched to run `bmad-create-story`
(fill the story with implementation context) then `bmad-dev-story` (implement, write
tests, commit) autonomously, reporting back per story.

The main loop records SHAs from git HEAD, never from Thor's report (relay-config
`§2.9`). It runs `git rev-parse HEAD` immediately before each dispatch
(`pre_sha`) and immediately after each report (`post_sha`). The story's
`baseline_commit` is the `pre_sha` of its first dev-story dispatch, cross-checked
against the `baseline_commit` dev-story writes to the story frontmatter.
`phase7_end_sha` is the `post_sha` of the dispatch that reports the story done.
After that report the main loop runs the `§2.9` checks (nothing committed,
ancestry, uncommitted source files, commit list) and writes both values to
`loop_state.stories[<story_key>]`. Phase 8 uses them to scope the story's review
range. In a repository with no commits yet, the first `pre_sha` is the empty-tree
hash; only a project that is not a git repository records `NO_VCS`.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
