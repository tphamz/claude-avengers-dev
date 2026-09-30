# BMAD Phase 8: Review & Completion (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Final phase.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | interactive + read-only verify |

## What happens

`bmad-code-review` halts for user choices, writes to the story file, and spawns
its own review subagents, so it runs in the main loop. The main loop never
applies patches — code changes always go to Thor. Per story:

1. **Code review (main loop).** Run `bmad-code-review` with the story file set as
   the spec. Resolve each `decision-needed` finding with the user at its step 4.
   At the patch menu, tell the user to pick **"Leave as action items"**, then
   **"Done"** at the next-steps menu. If the user picks "Apply every patch"
   anyway, stop and hand the patch list to Thor instead of applying it.
2. **Reconcile Review Findings (main loop).** In the story's `### Review Findings`:
   every decision the user converted to a patch is recorded as an unchecked
   `- [ ] [Review][Patch] ...` bullet; every resolved `[Review][Decision]` bullet
   is checked (`[x]`) or struck through. Unchecked Decision bullets make
   `bmad-dev-story` step 9 HALT.
3. **Fix (Thor).** If unchecked `[Review][Patch]` items exist after
   reconciliation, dispatch Thor with the explicit story file path (dev-story
   auto-discovery only picks `ready-for-dev` stories) and the `[Review][Patch]`
   items named one by one (the skill's review-continuation check looks for the
   older "Senior Developer Review (AI)" section). Thor runs `bmad-dev-story` on
   that path, resolves the items, runs tests and commits. Dev-story step 9 sets the
   story to `review`.
4. **Review (Captain).** Read `baseline_commit` from the story frontmatter
   (written by dev-story) and pass Captain the story file path and the concrete
   range `<baseline_commit>..HEAD`. Captain reviews read-only. Verdict: PASS |
   CONDITIONAL PASS | FAIL.
5. **Verify (BlackWidow).** BlackWidow checks Captain's findings for false
   positives.
6. **Cycle.** A FAIL, or a CONDITIONAL PASS (Warnings), goes back to Thor with the
   verified findings → Captain → BlackWidow. The limit is 3 cycles. After the
   third, the verdict goes to the user, who either accepts the CONDITIONAL PASS or
   exits (`status: suspended`). A FAIL cannot be accepted.
7. **Close-out (main loop).** After a PASS (or a user-accepted CONDITIONAL PASS at
   the cycle limit) and BlackWidow's verification, the main loop sets the story
   file's `Status: done` and, in `sprint-status.yaml`, sets
   `development_status[<story_key>]: done` (key = story file basename, e.g.
   `1-2-user-auth`) and `last_updated` to today, preserving all comments and
   structure. This is a BMAD artifact write under the wrapped-skill exception.
8. **Retrospective (main loop, at epic completion).** Epic N is complete when every
   story key for epic N (keys starting `N-`, excluding `epic-N` and
   `epic-N-retrospective`) is `done` in `sprint-status.yaml`. Only then run
   `bmad-retrospective` and relay its output. No Captain verification.

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
  `bmad-code-review`; Review Findings reconciliation and `Status: done` by the
  main loop; tasks, File List, Change Log and Status (`review`) by `bmad-dev-story`
  (Thor)
- `{implementation_artifacts}/deferred-work.md` — deferred findings, by `bmad-code-review`
- `{implementation_artifacts}/sprint-status.yaml` — story status by `bmad-dev-story`
  (`in-progress`, `review`) and by the main loop at close-out (`done`); epic
  retrospective status by `bmad-retrospective`. `bmad-code-review` does not sync
  it in this flow.
- `{implementation_artifacts}/epic-{N}-retro-{date}.md` — by `bmad-retrospective`

When every epic is complete (all story keys `done` in `sprint-status.yaml`) and
its retrospective has run, announce sprint completion and transition the sequence
to `complete` in the state file.

Authoring instructions and completion criteria are owned by the skills. See
`references/bmad/relay-config.md` for the full phase map.
