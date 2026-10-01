# BMAD: offer owed retrospectives on fresh Phase 8 entry

## Objective
Close the gap PRs #5 and #7 left in `/bmad` Phase 8: an epic whose stories were already `done` at a fresh Phase 8 entry is inferred `closed` and never gets a retrospective, while the resume-only sweep for "retrospectives still owed" is unscoped, records no decline, and leaves "owed" undefined. Define "in this sequence", "owed" and the retrospective offer once in relay-config `§3.13` step 8, run an epic close-out sweep (epic `done` sweep, then offers) on fresh entry and resume, and make the Phase 8 exit satisfiable.

## Scope

**Files to Create/Modify/Delete**
- `specs/stories/bmad-retro-sweep.md` — this spec
- `references/bmad/relay-config.md` — `loop_state` schema (`retros_declined`, `completed` wording), `§3.2` resume wording on `completed` and the post-loop sweep, `§3.13` step 8 canonical definitions
- `references/bmad/phase-8-review.md` — resume paragraph, step 8 + epic close-out sweep, artifacts, exit
- `skills/bmad/SKILL.md` — resume step 4, Phase 8 step 8, Phase 8 exit
- `agents/vision.md` — Phase 8 summary
- `equipment/schemes/bmad-sequence.md` — Phase 8 summary, Resume `completed` nuance, completion checklist
- `personas/ironman.md` — Phase 8 one-liner
- `CLAUDE.md` — Phase 8 one-liner

## Acceptance Criteria
- [ ] relay-config `§3.13` step 8 is the single canonical definition of "in this sequence" (a story key in `loop_state.completed`, a non-null `baseline_commit` with `NO_VCS` counting, or `review_cycles >= 1`), the legacy fallback (no `track`, or no `completed` entry matching a `development_status` key → every complete epic in scope), "owed" (complete, in this sequence, `epic-N-retrospective` exists and is not `done`, `"N"` not in `retros_declined`; a missing retro key is not owed), the offer, the epic close-out sweep and the exit
- [ ] The offer is "[1] Run retrospective for epic N / [2] Skip", names any existing `epic-N-retro-*.md`, passes N explicitly on [1], and on [2] appends `"N"` (a string) to `loop_state.retros_declined` and saves immediately; an abandoned [1] is offered again
- [ ] The epic close-out sweep runs after the story loop on fresh entry and resume, in order: epic `done` sweep (unchanged from PR #7), then the offer for each owed epic
- [ ] Exit: every complete epic in this sequence has had its retrospective run or declined
- [ ] `loop_state` schema lists `retros_declined: list  # epic numbers (strings) the user skipped`
- [ ] `completed` is described consistently: read by marker inference and the `§3.13` step 8 scope check, never for resume decisions (relay-config schema and `§3.2`, `bmad-sequence.md` Resume)
- [ ] Every other file references "`§3.13` step 8" with no parenthetical directly after the citation
- [ ] `python3 -m unittest discover -s tests` passes

## Tasks
- [ ] Save this spec
- [ ] Write the canonical step 8 text and schema field in relay-config; fix the two `completed` contradictions
- [ ] Update phase-8-review.md, SKILL.md, vision.md, bmad-sequence.md (including the checklist), ironman.md and CLAUDE.md to reference it
- [ ] Grep `owed`, `retros_declined`, `in this sequence` and `epic sweep` for consistency; run the test suite
- [ ] Commit `fix(bmad): offer owed retrospectives on fresh Phase 8 entry`
- [ ] Hand off for Captain review, BlackWidow verification, and a user debug session in a scratch project

## Engineering Notes (Hulk)
- Required: the `review_cycles >= 1` scope clause, so a story reviewed but not built in this sequence still pulls its epic in.
- Marker inference never writes `completed`, `baseline_commit` or `review_cycles`, so earlier-sequence stories cannot widen the scope.
- Upstream `bmad-retrospective` has no skip and writes `done` only after saving the retro doc; the decline therefore lives in relay state, and the offer names an existing retro doc to avoid a duplicate after a crash between the doc save and the status write.
- `retros_declined` holds strings so it matches the `N` parsed out of `epic-N` keys without type coercion.
- Citation trap: `test_doc_consistency` reads a parenthetical after `§N.N` as a section title; write "`§3.13` step 8".
- Behavior change for release notes: step 8 now asks before running the retrospective instead of running it immediately.

## Status
- [x] Spec approved by user
