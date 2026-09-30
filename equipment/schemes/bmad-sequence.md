# BMAD Sequence - Full Methodology Scheme

## When to Equip

Use when IronMan says "run BMAD", "start a BMAD sequence", or "use the BMAD
methodology" for a new initiative or sprint.

This scheme **wraps the real BMAD-METHOD `bmad-*` skills** and conducts them through
the crew in Vision's voice. It does not reimplement BMAD.

## The Crew — phase → real skill → owner → mode

| Phase | Real skill(s) | Owner | Mode |
| ----- | ------------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` / `bmad-investigate` | main loop; BlackWidow verifies | interactive + verify |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |
| 2 PRD | `bmad-prd` | main loop (Vision voice) | interactive |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; Hulk verifies | interactive + verify |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | light |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | Thor (per story) | autonomous |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, Captain reviews, BlackWidow verifies, main loop closes out | interactive + verify |

**Why the split:** the wrapped `bmad-*` skills ask the user questions and write
artifacts as they go. A subagent runs blind and cannot elicit, and BlackWidow,
Hulk and Captain are read-only, so every skill except the Phase 7 build runs in
the main loop and the owner verifies the result. The main loop writes BMAD
artifacts only — code changes, including code-review patches, always go to Thor.

## Design-Implementation Boundary

After Phase 5, the relay halts. IronMan presents both the readiness report's
status and Hulk's independent verdict; if either is NOT READY / NOT-READY, he
recommends [2]; if either is NEEDS WORK / READY-WITH-CONCERNS, he flags it
explicitly with the cited gaps. The user makes an explicit choice — **[1] Continue into
implementation / [2] Exit** — before Phase 6 begins. No auto-advance.

## Artifacts

Written by the wrapped `bmad-*` skills to paths set in `_bmad/bmm/config.yaml`:
`{project_knowledge}` (default `docs/`) for `bmad-document-project`;
`{planning_artifacts}` and `{implementation_artifacts}` (default under
`_bmad-output/`) for everything else. See `references/bmad/relay-config.md` §2.8.
The relay's own state file: `.avengers/relay-sequences/bmad-{name}.yaml`.

## Phase 8 Per-Story Flow

Code review (main loop, range `<baseline_commit>..<phase7_end_sha>`, "Leave as
action items") → reconcile `### Review Findings` inside Tasks/Subtasks (converted
decisions recorded as unchecked `[Review][Patch]`; resolved `[Review][Decision]`
checked `[x]`; sprint-status entry `in-progress`) → Thor fixes unchecked
`[Review][Patch]` items (explicit story path; fix range `<pre_sha>..<post_sha>`
recorded from HEAD) → Captain reviews `git diff` of
`<baseline_commit>..<phase7_end_sha>` and each fix range → BlackWidow verifies
(story path, same ranges, Captain's findings) → FAIL or CONDITIONAL PASS: verified
findings appended as unchecked `[Review][Patch]`, loops to Thor (max 3 Captain
verdicts in `review_cycles`, then the user accepts the CONDITIONAL
PASS or exits; a FAIL cannot be accepted) → close-out (main loop): story
`Status: done`, `sprint-status.yaml` entry `done` + `last_updated`. Epic N is
complete when every story key for epic N is `done` in `sprint-status.yaml`; only
then does `bmad-retrospective` run, with epic N passed explicitly. Per-story SHAs
and ranges (recorded by the main loop from `git rev-parse HEAD`, never from
Thor's report), `phase8_start_sha` and the cycle count live in the state file's
`loop_state` (relay-config `§2.9`, `§2.10`). See `references/bmad/phase-8-review.md`.

## Completion Criteria
- [ ] All phases completed (1a → 8)
- [ ] Design-implementation hard gate cleared with explicit user authorization
- [ ] All stories built (Thor) and reviewed (Captain)
- [ ] Captain verdict per story: PASS, or a CONDITIONAL PASS the user accepted at the 3-cycle limit
- [ ] Every story closed out: `done` in its story file and in `sprint-status.yaml`
- [ ] Retrospective run for each epic whose story keys are all `done`
- [ ] State file transitioned to `complete`
