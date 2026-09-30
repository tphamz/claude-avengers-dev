# BMAD Phase 7: Build (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Iterative, per-story.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-create-story` → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-dev-story` per story | interactive + build (HALTs relayed) |

## What happens

`bmad-create-story` stops for the user on every run (its checklist menu, missing
input offers) and wants web research, so it runs in the main loop. It writes only
the story file and `sprint-status.yaml`. `bmad-dev-story` changes source code, so
Thor runs it, and every stop that needs a human comes back as a Blocked report
for the main loop to relay. Per story, in `development_status` order (full detail
in relay-config `§3.8`):

1. **Create the story (main loop).** Skip if the story is already past
   `backlog`. Check the epic first: `backlog` or `contexted` → set it to
   `in-progress`; `done` → stop and ask the user; any other status except
   `in-progress` → stop. Run `Skill(bmad-create-story)` with the full
   `development_status` key (e.g. `1-2-user-auth`). The user answers its menus;
   the main loop does its web research. Afterwards, check that the story file and
   its `sprint-status.yaml` entry are both `ready-for-dev`, and stop if not.
2. **Record `pre_sha`** and resolve the story file path.
3. **Build (Thor).** `Agent(avengers-dev:thor)` runs `bmad-dev-story` on the
   explicit story file path. At any HALT or ask point he stops without
   committing and returns a Blocked report. dev-story's step-10 completion
   prompts are not stops: he finishes, runs tests, commits and reports done.
4. **Blocked.** Record `loop_state.stories[<story_key>].blocked`, relay the HALT
   point, question, options and work state to the user, and ask: answer or
   suspend. On an answer, for a step-9 gate HALT append an unchecked
   `- [ ] [Gate] Fix <failure>: <user answer>` subtask to `## Tasks / Subtasks`
   (except "File List is incomplete", which Thor fixes directly); if dev-story
   already set `review`, reset the story file and `sprint-status.yaml` to
   `in-progress`. Then clear `blocked` and re-dispatch Thor with the answer. No
   cap on this loop; real agent failures retry up to 2 times, then escalate.
5. **Done.** Record `post_sha`, run the `§2.9` checks, write `baseline_commit`
   and `phase7_end_sha`, and update `loop_state`.

## Commit tracking

The main loop records SHAs from git HEAD, never from Thor's report (relay-config
`§2.9`). It runs `git rev-parse HEAD` immediately before each dispatch
(`pre_sha`) and immediately after each report (`post_sha`). The story's
`baseline_commit` is the `pre_sha` of its first dev-story dispatch, cross-checked
against the `baseline_commit` dev-story writes to the story frontmatter.
`phase7_end_sha` is the `post_sha` of the dispatch that reports the story done,
so the range covers every Blocked re-dispatch. After that report the main loop
runs the `§2.9` checks (nothing committed, ancestry, uncommitted source files,
commit list) and writes both values to `loop_state.stories[<story_key>]`. Phase 8
uses them to scope the story's review range. In a repository with no commits yet,
the first `pre_sha` is the empty-tree hash; only a project that is not a git
repository records `NO_VCS`.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
