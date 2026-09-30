# BMAD Sequence - Full Methodology Scheme

## When to Equip

Use when IronMan says "run BMAD", "start a BMAD sequence", or "use the BMAD
methodology" for a new initiative or sprint.

This scheme **wraps the real BMAD-METHOD `bmad-*` skills** and conducts them through
the crew in Vision's voice. It does not reimplement BMAD.

Tracks: `quick` (0 → `bmad-quick-dev` → Captain diff review → 9), `standard`
(default), `full` (standard + ATDD in 7 and trace in 8; needs the TEA module).

## The Crew — phase → real skill → owner → tracks

| Phase | Real skill(s) | Owner | Tracks |
| ----- | ------------- | ----- | ------ |
| 0 KB check | `bmad-kb.py status` | main loop | all |
| 1a Discovery (if KB missing / stale + accepted) | `bmad-document-project` + `bmad-generate-project-context` → `stamp` | main loop (Vision voice); BlackWidow verifies | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` (+ optional validate / elicitation) | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | main loop; Captain (`adversarial` lens) verifies and assigns severity | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; Hulk verifies | standard, full |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full) → `bmad-dev-story` | main loop runs create-story; Thor runs atdd (full) and dev-story (per story, HALTs relayed) | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full) + `bmad-retrospective` | main loop; Thor fixes, Captain reviews, BlackWidow verifies, main loop closes out | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → refresh if confirmed → `stamp` | main loop (Vision voice) | all |

**Why the split:** the wrapped `bmad-*` skills ask the user questions and write
artifacts as they go. A subagent runs blind and cannot elicit, and BlackWidow,
Hulk and Captain are read-only, so every skill except `bmad-dev-story` (and
`bmad-testarch-atdd` on the full track) runs in the main loop (Phase 7's
`bmad-create-story` included) and the owner verifies the result. Thor runs
`bmad-dev-story` (after atdd on the full track); when it stops for a human he returns a
Blocked report and the main loop relays it to the user. The main loop writes BMAD
artifacts and relay bookkeeping only (list in relay-config §3.10) — code changes,
including code-review patches, always go to Thor.
**Quick-track exception:** on the `/bmad` quick track, `bmad-quick-dev` runs in the
main loop and implements the code; it is the one sanctioned case where the main
loop writes source code (Captain's fixes still go to Thor by default).

## Design-Implementation Boundary

After Phase 5, the relay halts. IronMan presents both the readiness report's
status and Hulk's independent verdict, plus any unresolved Phase 4.5 Criticals;
if either result is NOT READY / NOT-READY, he recommends [2]; if either is NEEDS
WORK / READY-WITH-CONCERNS, he flags it explicitly with the cited gaps. The user
makes an explicit choice — **[1] Continue into implementation / [2] Exit** —
before Phase 6 begins. No auto-advance. If either result is NOT READY / NOT-READY
or Phase 4.5 Criticals are unresolved, [1] needs `override` plus a reason.

## Artifacts

Written by the wrapped `bmad-*` skills to paths set in `_bmad/bmm/config.yaml`:
`{project_knowledge}` (default `docs/`) for `bmad-document-project`;
`{planning_artifacts}` and `{implementation_artifacts}` (default under
`_bmad-output/`) for everything else. See `references/bmad/relay-config.md` §2.8.
The relay's own state file: `.avengers/relay-sequences/bmad-{name}.yaml`.

## Phase 7 Per-Story Flow

Only stories at `phase7_step: recorded` are skipped (a resume replays a stored
`blocked` question to the user before any dispatch) → create-story skipped if the story is past `backlog`;
otherwise the epic status check (`backlog`/`contexted` → `in-progress`;
`in-progress` → no change; `done` → stop and ask; anything else → stop) →
`bmad-create-story` in the main loop with the full `development_status` key
(story and sprint-status entry verified `ready-for-dev`) → `pre_sha` recorded,
`in_progress` set, `baseline_commit` written before the first dispatch → Thor
runs `bmad-testarch-atdd` (full track) then `bmad-dev-story` on the explicit
story path → Blocked: stored in `blocked`,
relayed to the user (answer or suspend), `[Gate]` subtask for a step-9
regression or definition-of-done HALT, `review` reset to `in-progress`,
re-dispatch with the answer, Work state and Resume instruction → done:
`post_sha` recorded, checks run, `phase7_end_sha` written (never overwritten).
See `references/bmad/relay-config.md` §3.12.

## Phase 8 Per-Story Flow

Code review (main loop, range `<baseline_commit>..<phase7_end_sha>`, "Leave as
action items"; full track: then `bmad-testarch-trace`, uncovered ACs become
`[Review][Patch]`) → reconcile `### Review Findings` inside Tasks/Subtasks (converted
decisions recorded as unchecked `[Review][Patch]`; resolved `[Review][Decision]`
checked `[x]`; sprint-status entry `in-progress`) → Thor fixes unchecked
`[Review][Patch]` items (explicit story path; Blocked reports handled as in
Phase 7; `chain_start_sha` written before the chain's first dispatch; fix range
`<chain_start_sha>..<done post_sha>` recorded from HEAD) → Captain reviews `git diff` of
`<baseline_commit>..<phase7_end_sha>` and each fix range → BlackWidow verifies
(story path, same ranges, Captain's findings) → FAIL or CONDITIONAL PASS: verified
findings appended as unchecked `[Review][Patch]`, loops to Thor (max 3 Captain
verdicts in `review_cycles`, then the user accepts the CONDITIONAL
PASS or exits; a FAIL cannot be accepted) → close-out (main loop): story
`Status: done`, `sprint-status.yaml` entry `done` + `last_updated`. Epic N is
complete when every story key for epic N (at least one) is `done` in
`sprint-status.yaml`; the
main loop then sets `epic-N: done` (upstream leaves it manual; the relay never
downgrades it), and only then does `bmad-retrospective` run, with epic N passed
explicitly. Before Phase 9 (and on resume, after the story loop and before any
owed retrospective), a sweep sets `epic-N: done` for every complete epic (as
defined above) whose `epic-N` entry is not `done`. Per-story SHAs
and ranges (recorded by the main loop from `git rev-parse HEAD`, never from
Thor's report), `phase8_start_sha` and the cycle count live in the state file's
`loop_state` (relay-config `§2.9`, `§2.10`). See `references/bmad/phase-8-review.md`.

## Resume

Resume uses per-story markers, `phase7_step` and `phase8_step`, not
`loop_state.completed` (stories with no marker get one from marker inference
first). Phase 7 skips `recorded`; Phase 8 skips `closed` and
re-enters every other story at its recorded step. See relay-config `§3.2` and
`§3.13`.

## Completion Criteria
- [ ] All phases for the chosen track completed (Phase 0 through Phase 9)
- [ ] Design-implementation hard gate cleared with explicit user authorization
      (any override recorded with a reason)
- [ ] All stories built (Thor) and reviewed (Captain)
- [ ] Captain verdict per story: PASS, or a CONDITIONAL PASS the user accepted at the 3-cycle limit
- [ ] Every story closed out: `done` in its story file and in `sprint-status.yaml`
- [ ] Each completed epic set to done in sprint-status.yaml
- [ ] Retrospective run for each epic whose story keys are all `done`
- [ ] Phase 9 KB refresh evaluated (refreshed and stamped, or not needed)
- [ ] State file transitioned to `complete`
