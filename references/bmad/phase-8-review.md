# BMAD Phase 8: Review (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Last implementation phase; advances to Phase 9 (KB Refresh).

| Real skill(s) | Owner | Mode | Tracks |
| ------------- | ----- | ---- | ------ |
| `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | interactive + read-only verify | standard |
| `bmad-code-review` + `bmad-testarch-trace` + `bmad-retrospective` | same; the main loop also runs `bmad-testarch-trace` | interactive + read-only verify | full |

## What happens

`bmad-code-review` halts for user choices, writes to the story file, and spawns
its own review subagents, so it runs in the main loop. The main loop never
applies patches — code changes always go to Thor.

Per-story commit tracking lives in the state file's `loop_state.stories`
(relay-config): `baseline_commit`, the Phase 7 end SHA (`phase7_end_sha`), each
Phase 8 fix range (`phase8_fix_ranges`), and the review cycle count
(`review_cycles`, `§2.10`). The main loop records all of them from
`git rev-parse HEAD`, never from the SHA in Thor's report (`§2.9`). The story's
review ranges are `<baseline_commit>..<phase7_end_sha>` plus each range in
`phase8_fix_ranges`. `<baseline_commit>..HEAD` is never used: Phase 7 builds every
story before Phase 8 starts, so it would include every later story's work.
When a range's left side is the empty-tree hash (a repository that had no commits
at Phase 7 start), diff, list commits and skip the ancestor check as relay-config
`§2.9` **Unborn HEAD** says; that is the one place the rule is stated.

**On entry**, before any Phase 8 dispatch, the main loop writes
`phase8_start_sha` (`git rev-parse HEAD`) to `loop_state` once, and sets
`phase8_step: pending` only on stories still unmarked after marker inference
(relay-config State Schema), which runs first, when the state file is read; a
story whose `development_status` entry is `done` is inferred `closed` and never
set to `pending`, and a resume keeps the recorded values. Each story's `phase8_step` (`pending` → `code_review_done` → `fixing` →
`captain` → `verify` → `closed`) is saved the moment it changes (relay-config
`§3.13`).

**Resume** (relay-config `§3.2`). First replay any story's stored `blocked`
entry to the user (answer or keep suspended) before any dispatch; when the
replayed fix chain reports done, record its fix range and continue at step 4.
A story with `chain_start_sha` set, no `blocked` and `phase8_step: fixing` is an
orphaned fix chain: ask the user whether to re-dispatch Thor to finish it or to
treat it as done (then record `<chain_start_sha>..<HEAD now>` after the `§2.9`
checks and continue at step 4). Then per story: `closed` → skip; `pending` →
step 1; `code_review_done` or `fixing` → step 2 only if not already done, then
step 3 if unchecked `[Review][Patch]` or `[Gate]` items remain, else step 4;
`captain` → step 4; `verify` → step 5 with the stored `captain_findings`. Code
review never re-runs past `pending`, a `closed` story is never set back to
`in-progress`, and `review_cycles` carries over unchanged. After the loop, run
the epic sweep, then any retrospective still owed (both step 8).
**Resume fallback:** if `loop_state.stories` has no
`phase7_end_sha` for a story (including a story marker inference set to
`recorded`), its `baseline_commit` comes from `loop_state`,
else from the story frontmatter (a frontmatter `NO_VCS` in a git repository means
the empty-tree hash), and its end is the next story's `baseline_commit`
(`development_status` order); the last story ends at `phase8_start_sha`. If the
stories are not in build order or the baselines do not chain, stop and ask the
user (`§2.9`). Per story:

1. **Code review (main loop).** Run `bmad-code-review` with the story file set as
   the spec and the story's explicit range `<baseline_commit>..<phase7_end_sha>`
   (its step 1 Tier 1 accepts a `<from-sha>..<to-sha>` range with a spec file;
   without one it diffs from `baseline_commit` and picks up later stories; with
   `NO_VCS` there is no range, so pick the diff source at its prompt).
   Resolve each `decision-needed` finding with the user at its step 4.
   At the patch menu, tell the user to pick **"Leave as action items"**, then
   **"Done"** at the next-steps menu. If the user picks "Apply every patch"
   anyway, stop and hand the patch list to Thor instead of applying it.
   **Full track only:** after "Done", run `bmad-testarch-trace` for the story in
   the main loop to map every acceptance criterion to a test. Right after it,
   the main loop writes each AC the trace reports untested into the story's
   `### Review Findings` (inside `## Tasks / Subtasks`; created there if code
   review wrote none) as an unchecked
   `- [ ] [Review][Patch] Cover AC <n>: <AC text, short>` bullet, skipping any
   `Cover AC <n>` bullet already present, so it loops back through Thor. Then,
   in one state write, it records `trace_report: <report path>` in
   `loop_state.stories[<story_key>]` and sets `code_review_done`.
   Runs only at `phase8_step: pending`; on the standard track, set
   `code_review_done` after "Done". **Resume at `code_review_done` (full
   track):** if `trace_report` is recorded but some untested AC in that report
   has no matching `Cover AC <n>` bullet, re-derive the missing bullets from the
   report before step 2; the trace never re-runs (relay-config `§3.2`).
2. **Reconcile Review Findings (main loop).** In the story's `### Review Findings`:
   every decision the user converted to a patch is recorded as an unchecked
   `- [ ] [Review][Patch] ...` bullet; every resolved `[Review][Decision]` bullet
   is checked (`[x]`). Striking the text through is optional and does not replace
   `[x]`. Unchecked Decision bullets make `bmad-dev-story` step 9 HALT. Make sure
   `### Review Findings` sits inside `## Tasks / Subtasks` (before `## Dev Notes`)
   — code-review only says to "append" it, and dev-story looks for unchecked
   tasks only in Tasks/Subtasks. Merge any duplicate `### Review Findings`
   section (a re-run code review appends a second one) into one, keeping each
   bullet once. Trace output is not converted here: step 1 already wrote the
   `Cover AC` bullets, so this step only dedupes against them. On a resume at
   `code_review_done` with unchecked
   `[Review][Decision]` bullets, the code-review conversation is lost: ask the
   user to decide each one directly. Set the story's `sprint-status.yaml` entry to
   `in-progress` so dev-story does not warn "Unexpected story status". A resume
   skips this step if it is already done (relay-config `§3.13`). No unchecked
   `[Review][Patch]` or `[Gate]` items → set `captain` and go to step 4.
3. **Fix (Thor).** If unchecked `[Review][Patch]` items exist after
   reconciliation, dispatch Thor with the explicit story file path (dev-story
   auto-discovery only picks `ready-for-dev` stories) and the `[Review][Patch]`
   items named one by one (the skill's review-continuation check looks for the
   older "Senior Developer Review (AI)" section). Thor runs `bmad-dev-story` on
   that path, resolves the items, runs tests and commits. Dev-story step 9 sets the
   story to `review`. The dispatch carries the same stop instruction as Phase 7:
   at any dev-story HALT or ask point, Thor stops without committing and returns
   a Blocked report. The main loop handles it as in relay-config `§3.12` step 4:
   record `blocked` (with options, work state and resume instruction), relay it
   to the user (answer or suspend), append a
   `- [ ] [Gate] Fix <failure>: <user answer>` subtask for a step-9 regression
   or definition-of-done HALT, reset the story and `sprint-status.yaml` to
   `in-progress` if dev-story set `review`, and re-dispatch with the answer, the
   previous Work state and the Resume instruction. Blocked re-dispatches do not
   count toward `review_cycles`. The main loop records `pre_sha` before every
   dispatch and `post_sha` after every report. Before the chain's first dispatch
   it writes that `pre_sha` as the story's `chain_start_sha` (kept if already
   set, and untouched when `blocked` is cleared) and sets `phase8_step: fixing`,
   in one write. On the done report it runs the `§2.9` checks and appends
   `<chain_start_sha>..<done post_sha>` (spanning any Blocked re-dispatches) to
   the story's `phase8_fix_ranges` in `loop_state.stories[<story_key>]`, then
   sets `chain_start_sha` to null and `phase8_step: captain` in the same write,
   and continues at step 4. (Phase 7 step 5 does not apply to a fix chain.)
4. **Review (Captain).** Pass Captain the story file path and the story's ranges
   from `loop_state`: `<baseline_commit>..<phase7_end_sha>` plus each range in
   `phase8_fix_ranges`, each reviewed with `git diff <range>` (an empty-tree
   left side follows `§2.9` **Unborn HEAD**). If
   `baseline_commit` is `NO_VCS`, pass the story's File List instead; Captain
   reviews those files as they stand now. Captain reviews read-only. Verdict:
   PASS | CONDITIONAL PASS | FAIL. The main loop then increments `review_cycles`,
   stores the verdict and findings in `captain_findings`, sets
   `phase8_step: verify`, and saves the state file in one write (`§2.10`).
5. **Verify (BlackWidow).** Pass BlackWidow the story file path, the same ranges
   (or File List) Captain received, and Captain's findings. She checks the
   findings for false positives.
6. **Cycle.** A FAIL, or a CONDITIONAL PASS (Warnings), goes back to Thor. First
   the main loop appends the verified Captain and BlackWidow findings to the
   story's `### Review Findings` as unchecked `- [ ] [Review][Patch] ...` bullets
   (dev-story implements only story tasks; findings already present are not
   added again) and sets the `sprint-status.yaml` entry to `in-progress`; then it
   sets `phase8_step: fixing` and Thor runs as in step 3 → Captain → BlackWidow.
   The limit is 3 cycles, one per Captain verdict, counted in `review_cycles` so
   it survives a resume. After
   the third, the verdict goes to the user, who either accepts the CONDITIONAL
   PASS or exits (`status: suspended`). A FAIL cannot be accepted.
7. **Close-out (main loop).** After a PASS (or a user-accepted CONDITIONAL PASS at
   the cycle limit) and BlackWidow's verification, the main loop sets the story
   file's `Status: done` and, in `sprint-status.yaml`, sets
   `development_status[<story_key>]: done` (key = story file name without `.md`,
   e.g. `1-2-user-auth`) and `last_updated` to today, preserving all comments and
   structure. This is a BMAD artifact write under the wrapped-skill exception.
   Then set `phase8_step: closed` and save. A `closed` story is never reopened.
8. **Epic done + retrospective (main loop, at epic completion).** Epic N is
   complete when every story key for epic N (keys starting `N-`, excluding
   `epic-N` and `epic-N-retrospective`; at least one) is `done` in
   `sprint-status.yaml`. Then the main loop first sets
   `development_status["epic-N"]: done` and `last_updated` to today, preserving
   all comments and structure (skip if already `done`). Upstream leaves this to
   a human: the `bmad-sprint-planning` sprint-status header marks
   `in-progress → done` as manual, and no `bmad-*` skill writes it. The relay
   never downgrades `epic-N`; only the user reopens it (Phase 7's `done` → stop
   and ask). Only then run `bmad-retrospective` with epic N passed explicitly
   (its auto-detection picks the highest epic with any `done` story) and relay
   its output. No Captain verification. **Epic sweep:** before advancing to
   Phase 9 (fresh entry or resume), set `epic-N: done` the same way for every
   epic whose story keys are all `done` and whose entry is not `done`; on
   resume the sweep runs before any owed retrospective.

**Why close-out exists:** code-review sets the story `in-progress` when patches are
left as action items, and dev-story sets it to `review`. Neither sets `done` in
this flow. And because the story is passed as the spec file, code-review never
sets `{story_key}`, so its own `sprint-status.yaml` sync is skipped. The
retrospective counts only `done` stories, so without close-out no epic would ever
complete.

## Artifacts written

Paths resolve from `_bmad/bmm/config.yaml` (relay-config `§2.8`):

- Story file — `### Review Findings` subsection (`[Review][Decision]`,
  `[Review][Patch]`, `[Review][Defer]` items) and Status (`in-progress`) by
  `bmad-code-review`; Review Findings reconciliation, appended Captain findings,
  `[Gate]` subtasks and `in-progress` resets after a Blocked report, and
  `Status: done` by the main loop; tasks, File List, Change Log and Status
  (`review`) by `bmad-dev-story` (Thor)
- `{implementation_artifacts}/deferred-work.md` — deferred findings, by `bmad-code-review`
- `{implementation_artifacts}/sprint-status.yaml` — story status by `bmad-dev-story`
  (`in-progress`, `review`) and by the main loop (`in-progress` before each Thor
  fix and after a Blocked report, `done` at close-out); epic status (`done`) by
  the main loop at step 8 and in the epic sweep; epic retrospective status by
  `bmad-retrospective`.
  `bmad-code-review` does not sync it in this flow.
- `{implementation_artifacts}/epic-{N}-retro-{date}.md` — by `bmad-retrospective`
- Traceability matrix and gate decision (full track) — by `bmad-testarch-trace`,
  at the path it resolves; the main loop records that path as the story's
  `trace_report` in `loop_state` and writes its untested ACs as `Cover AC <n>`
  bullets in the story's `### Review Findings` (step 1)

When every epic is complete (all story keys `done` in `sprint-status.yaml`) and
its retrospective has run, run the epic sweep (step 8) so every completed epic
is `done`, then announce sprint completion and advance to **Phase 9**.
Phase 8 no longer sets `complete`; Phase 9 does.

Authoring instructions and completion criteria are owned by the skills. See
`references/bmad/relay-config.md` for the full phase map.
