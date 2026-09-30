# BMAD: HEAD-based review ranges + Phase 7 create-story in main loop with dev-story HALT relay

## Objective
Record every BMAD review range from `git rev-parse HEAD` in the main loop instead of Thor's reported SHA, and fix Phase 7 so the interactive `bmad-create-story` runs in the main loop while `bmad-dev-story` HALTs are relayed to the user via a Thor Blocked report.

## Scope

**Files to Create/Modify/Delete**
- `specs/stories/bmad-head-ranges-phase7-halts.md` — this spec (commit 1)
- `skills/bmad/SKILL.md` — description, line 22, table row 44, seam 47-51, Phase 7 142-147, Phase 8 fix/review ranges, 226-229; WebSearch/WebFetch in allowed-tools
- `references/bmad/relay-config.md` — schema (baseline from pre_sha, phase8_fix_ranges, phase8_start_sha, blocked, review_cycles rule, legacy migration), 19-22, 34, 121-125, 138-139, 158-159
- `references/bmad/phase-7-stories.md` — new per-story sequence
- `references/bmad/phase-8-review.md` — ranges, resume fallback, Blocked handling in step 3
- `agents/thor.md` — Blocked Report template, wrapped-skill stop rule with step-10 exemption, NO_VCS no-commit line, no commit on Blocked
- `agents/captain.md` — `git diff <range>` per fix range (88-92)
- `agents/blackwidow.md` — Phase 8 dispatch receives story path, ranges, Captain findings (88)
- `agents/vision.md` — Phase 7/8 text, table row 66
- `equipment/schemes/bmad-sequence.md` — row 22, 27, 49-54
- `personas/ironman.md` — A2 list 114-118, 213-215, 225-226
- `.claude/rules/ironman-delegation.md` — A2 list 24-25
- `scripts/compact-resume.sh` — A2 line 16
- `CLAUDE.md` — 31-33, 111-112

## Acceptance Criteria
- [ ] Main loop runs `git rev-parse HEAD` before every Thor dispatch (pre_sha) and after every report (post_sha); no range anywhere derives from Thor's reported SHA
- [ ] loop_state baseline_commit = pre_sha of the story's first Phase 7 dev-story dispatch, cross-checked against story frontmatter
- [ ] A Phase 8 fix range spans the first pre_sha to the done-report post_sha across any Blocked re-dispatches; `phase8_fix_shas` renamed `phase8_fix_ranges` with legacy `<sha>` read as `<sha>^..<sha>`
- [ ] "Nothing committed" flag fires only on done reports and never under NO_VCS; ancestor check and dirty-source-tree check run after each done report
- [ ] Unborn HEAD in a git repo uses the empty-tree hash as baseline; only a non-repo records NO_VCS
- [ ] `phase8_start_sha` written once at Phase 8 entry and used as the last story's resume-fallback end; mismatched chains stop and ask the user
- [ ] `review_cycles` definition written in relay-config and consistent with CLAUDE.md / ironman.md; Blocked re-dispatches do not count
- [ ] create-story runs in the main loop with the full sprint-status key; epic pre-check (backlog/contexted -> in-progress, done -> stop); skipped if story is past backlog; post-check verifies story file + sprint-status are ready-for-dev
- [ ] Thor Blocked report exists in agents/thor.md; dev-story step 10 prompts are explicitly not stops; Thor does not commit on Blocked
- [ ] Step-9 gate HALTs: main loop appends an unchecked `[Gate]` subtask under Tasks/Subtasks and resets status to in-progress before re-dispatch; same handling in Phase 8 step 3
- [ ] A2 carve-out lists the epic-status write and Blocked resets in ironman.md, ironman-delegation.md, compact-resume.sh
- [ ] No `tools:` frontmatter changed; `bash -n` passes on scripts/*.sh
- [ ] `grep -rn "bmad-create-story"` hits only main-loop contexts; `grep -rn "git show"` has no Phase 8 fix-commit usage; `phase8_fix_shas` appears only in the migration note

## Tasks
- [ ] Commit 1 `fix(bmad): record review ranges from git HEAD, not Thor's report`: save this spec; range/baseline/NO_VCS/unborn-HEAD/resume/review_cycles changes across SKILL.md, relay-config, phase-7, phase-8, vision, captain, blackwidow, bmad-sequence, ironman, CLAUDE.md, thor.md (NO_VCS line)
- [ ] Commit 2 `fix(bmad): run create-story in main loop; relay dev-story HALTs to the user`: Phase 7 sequence, Blocked report + rules in thor.md, step-9 [Gate] task rule, Phase 8 step 3 Blocked handling, A2 carve-out in ironman.md / ironman-delegation.md / compact-resume.sh, mode tables and seam comments
- [ ] Run the grep checks above and `bash -n scripts/*.sh`
- [ ] Hand off for Captain review, BlackWidow verification, and a user debug session in a scratch project with `npx bmad-method install` (one epic, two stories), exercising Phase 7 through Phase 8

## Engineering Notes (Hulk)
- Blocking finding: step-9 gate HALTs livelock on re-dispatch (dev-story step 1 L203 jumps to step 9 when all tasks are checked; L337 forbids unmapped work). The [Gate] subtask amendment is required.
- create-story is artifact-only (story file and sprint-status.yaml; on_complete empty by default), so it fits A2 once the carve-out wording is extended beyond "while a wrapped skill runs".
- The explicit story key must be the full sprint-status key, or create-story step 6 misses the entry and dev-story step 4 never writes baseline_commit.
- A debug session in the plugin repo stops at BMAD_MISSING, so a scratch project is required to validate Phase 7/8. CLEAN is a pre-PR gate here, which departs from development-standards "before committing".
- Out of scope here: setting epic-N done. Handled by the follow-up (branch claude/bmad-epic-done): the main loop sets epic-N done at Phase 8 step 8, plus a pre-Phase-9 sweep.

## Status
- [x] Spec approved by user

## Implementation Notes (post-approval review cycles)
- The `§2.9` checks run on the whole chain range `<chain start>..<post_sha>` (`baseline_commit` or `chain_start_sha`), not on the last dispatch alone. Check 4 flags only commits that no report in the chain mentioned.
- Check 3 (uncommitted work) flags only paths in the story's File List or Thor's reported files, using `git status --porcelain -z --untracked-files=all` with repo-root-relative paths. Relay state and BMAD artifacts are ignored.
- Resume uses per-story markers instead of status-based skipping: `phase7_step` (`pending | dispatched | done_reported | recorded`) and `phase8_step` (`pending | code_review_done | fixing | captain | verify | closed`), with `captain_findings` kept for a resume at `verify`.
- `blocked` stores `halt_point`, `question`, `options`, `work_state`, `resume_instruction` and `dispatched_at_sha`, so a resumed replay carries the full Blocked context.
- The empty-tree hash is computed with `git hash-object -t tree /dev/null` rather than hardcoded.
- Marker inference runs when the state file is read, before any phase entry step: a story with no `phase7_step` is `recorded` if it is in `loop_state.completed`, at `review` or `done`, or has a `phase7_end_sha` (else `dispatched` with a `baseline_commit`, else `pending`), and a `done` story with no `phase8_step` is `closed`, so stories from an earlier sequence are never rebuilt or re-reviewed.
