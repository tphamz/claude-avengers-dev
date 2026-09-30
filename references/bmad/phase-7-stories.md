# BMAD Phase 7: Build (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Iterative, per-story.

| Real skill(s) | Owner | Mode | Tracks |
| ------------- | ----- | ---- | ------ |
| `bmad-create-story` → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-dev-story` per story | interactive + build (HALTs relayed) | standard |
| `bmad-create-story` → `bmad-testarch-atdd` → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-testarch-atdd` then `bmad-dev-story` per story | interactive + build (HALTs relayed) | full |

## What happens

`bmad-create-story` stops for the user on every run (its checklist menu, missing
input offers) and wants web research, so it runs in the main loop. It writes only
the story file and `sprint-status.yaml`. `bmad-dev-story` changes source code, so
Thor runs it, and every stop that needs a human comes back as a Blocked report
for the main loop to relay. Per story, in `development_status` order, skipping
only a story whose `loop_state.stories[<story_key>].phase7_step` is `recorded`
(full detail in relay-config `§3.12`; the marker is `pending` → `dispatched` →
`done_reported` → `recorded`, each saved immediately):

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
   existing one. Set `phase7_step: dispatched` and save before dispatching.
3. **Build (Thor).** `Agent(avengers-dev:thor)` runs `bmad-dev-story` on the
   explicit story file path. **Full track only:** in the same dispatch, before
   dev-story, he runs `bmad-testarch-atdd` (write failing acceptance tests from
   the story's ACs; skipped on a re-dispatch once those tests exist), so the
   tests are part of the story's chain range. At any HALT or ask point he stops
   without committing and returns a Blocked report. dev-story's step-10 completion
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
5. **Done.** On the done report set `phase7_step: done_reported` and save,
   before any check. Then record `post_sha`, run the `§2.9` checks, write
   `phase7_end_sha` (never overwriting one), update `loop_state`, and set
   `phase7_step: recorded` in the same write.

**Resume** (relay-config `§3.2`). Before any dispatch, a story with a stored
`blocked` entry is replayed to the user (question and options: answer or keep
suspended); an answer continues at step 4's answer path, and when that chain
reports done it continues at step 5. Then, per story: `recorded` → skip;
`pending` → step 1; `done_reported`, or `dispatched` with no `blocked` and the
story at `review` → take `post_sha` from HEAD now, run the `§2.9` checks, do
step 5, and tell the user the range was recovered; `dispatched` with no
`blocked` and not at `review` → an interrupted dispatch, re-dispatched at step 2
as an agent-failure retry.

The full track requires the TEA module (`_bmad/tea/`), checked by
`bmad-kb.py preflight --track full` before the sequence starts.

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
HEAD**, computed with `git hash-object -t tree /dev/null`); only a project that is not a git repository records `NO_VCS`.

## Scope Creep

If implementation surfaces out-of-scope requirements, surface 3 options to the user
(defer / pause-replan / add-informally). Do not implement out-of-scope items
silently. See `references/bmad/relay-config.md` §3.7.

Authoring instructions and completion criteria are owned by the skills.
