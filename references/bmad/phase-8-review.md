# BMAD Phase 8: Review & Completion (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Final phase.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies | interactive + read-only verify |

## What happens

`bmad-code-review` halts for user choices, writes to the story file and sprint
tracking, and spawns its own review subagents, so it runs in the main loop. The
main loop never applies patches — code changes always go to Thor. Per story:

1. **Code review (main loop).** Run `bmad-code-review` with the story file set as
   the spec. At the patch menu, tell the user to pick **"Leave as action items"**,
   then **"Done"** at the next-steps menu. If the user picks "Apply every patch"
   anyway, stop and hand the patch list to Thor instead of applying it.
2. **Fix (Thor).** If the story has unchecked `[Review][Patch]` items, dispatch
   Thor to run `bmad-dev-story` on that story, resolving those items (name them
   explicitly — the skill's review-continuation check looks for the older
   "Senior Developer Review (AI)" section), then run tests and commit.
3. **Review (Captain).** Captain reviews the story's changes read-only. Verdict:
   PASS | CONDITIONAL PASS | FAIL.
4. **Verify (BlackWidow).** BlackWidow checks Captain's findings for false
   positives.
5. **Loop.** On FAIL, back through Thor → Captain → BlackWidow, max 3 cycles, then
   escalate to the user.
6. **Retrospective (main loop, at epic completion).** Run `bmad-retrospective`
   and relay its output. No Captain verification.

## Artifacts written

Paths resolve from `_bmad/bmm/config.yaml` (relay-config `§2.8`):

- Story file — `### Review Findings` subsection (`[Review][Decision]`,
  `[Review][Patch]`, `[Review][Defer]` items) and the Status section
  (`done` or `in-progress`), by `bmad-code-review`
- `{implementation_artifacts}/deferred-work.md` — deferred findings, by `bmad-code-review`
- `{implementation_artifacts}/sprint-status.yaml` — story status sync by
  `bmad-code-review`; epic retrospective status by `bmad-retrospective`
- `{implementation_artifacts}/epic-{N}-retro-{date}.md` — by `bmad-retrospective`

On a clean verdict for every story, announce sprint completion and transition the
sequence to `complete` in the state file.

Authoring instructions and completion criteria are owned by the skills. See
`references/bmad/relay-config.md` for the full phase map.
