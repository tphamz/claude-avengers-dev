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
for the main loop to relay. Per story, in `development_status` order, skipping
any story that is `review` or `done` in `sprint-status.yaml` or listed in
`loop_state.completed`, unless it is a suspended Blocked story (full detail in
relay-config `§3.8`):

1. **Create the story (main loop).** Skip if the story is already past
   `backlog`. Otherwise check the epic first: `backlog` or `contexted` → set it
   to `in-progress`; `in-progress` → no change; `done` → stop and ask the user;
   anything else → stop. Run `Skill(bmad-create-story)` with the full
   `development_status` key (e.g. `1-2-user-auth`). The user answers its menus;
   the main loop does its web research. Afterwards, check that the story file and
   its `sprint-status.yaml` entry are both `ready-for-dev`, and stop if not.
2. **Record `pre_sha`**, resolve the story file path, and set
   `loop_state.in_progress` to the story. Before the story's first dispatch,
   write that `pre_sha` to `loop_state` as `baseline_commit`; never overwrite an
   existing one.
3. **Build (Thor).** `Agent(avengers-dev:thor)` runs `bmad-dev-story` on the
   explicit story file path. At any HALT or ask point he stops without
   committing and returns a Blocked report. dev-story's step-10 completion
   prompts are not stops: he finishes, runs tests, commits and reports done.
4. **Blocked.** Record `loop_state.stories[<story_key>].blocked` (HALT point,
   question, options, work state, resume instruction, `dispatched_at_sha`),
   relay the HALT point, question, options and work state to the user, and ask:
   answer or suspend. On an answer, for a step-9 regression or
   definition-of-done HALT append an unchecked
   `- [ ] [Gate] Fix <failure>: <user answer>` subtask to `## Tasks / Subtasks`
   (none for "any task is incomplete", whose unchecked task already resumes
   dev-story, or "File List is incomplete", which Thor fixes directly); if
   dev-story already set `review`, reset the story file and `sprint-status.yaml`
   to `in-progress`. Then clear `blocked` (the chain start stays in
   `baseline_commit`) and re-dispatch Thor with the answer, the previous Work
   state and the Resume instruction. No cap on this loop; real agent failures
   retry up to 2 times, then escalate.
5. **Done.** Record `post_sha`, run the `§2.9` checks, write `phase7_end_sha`
   (never overwriting one), and update `loop_state`.

**Resume.** Before any dispatch, a story with a stored `blocked` entry is
replayed to the user (question and options: answer or keep suspended); an answer
continues at step 4's answer path (relay-config `§3.2`).

## Commit tracking

The main loop records SHAs from git HEAD, never from Thor's report (relay-config
`§2.9`). It runs `git rev-parse HEAD` immediately before each dispatch
(`pre_sha`) and immediately after each report (`post_sha`). The story's
`baseline_commit` is the `pre_sha` of its first dev-story dispatch, written to
`loop_state` before that dispatch and cross-checked against the
`baseline_commit` dev-story writes to the story frontmatter. `phase7_end_sha` is
the `post_sha` of the dispatch that reports the story done, so the range covers
every Blocked re-dispatch. After that report the main loop runs the `§2.9`
checks (nothing committed, ancestry, uncommitted story files, commit list) and
writes `phase7_end_sha` to `loop_state.stories[<story_key>]`. The
uncommitted-files check flags only paths in the story's File List or Thor's
reported files; if it flags, Thor's commit dispatch joins the same chain, and the
main loop takes `post_sha` again, reruns the checks and records it. Phase 8 uses
these values to scope the story's review range. In a repository with no commits
yet, `rev-parse` fails and the empty-tree hash stands in (`§2.9` **Unborn
HEAD**); only a project that is not a git repository records `NO_VCS`.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
