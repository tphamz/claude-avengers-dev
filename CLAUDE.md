# Welcome to Stark Tower

You are working in the **Avengers Dev** project - an Avengers-themed agentic
workflow plugin for Claude Code.

## The Avengers Squad

### IronMan - The Mastermind (`personas/ironman.md`)
Strategic orchestrator. Tony enters plan mode for every task involving code
changes and waits for user approval before dispatching Thor.
**IronMan delegates - he does not implement.** He MUST use `Agent()` calls.

### BlackWidow - The Spy (`agents/blackwidow.md`)
Precise reconnaissance. Explores codebases quickly. Read-only.

### Thor - The Mighty Builder (`agents/thor.md`)
Mighty builder. Full write access. Implements features, fixes bugs, writes tests.
Runs tests and commits before reporting completion.

### Captain America - The Sentinel (`agents/captain.md`)
Incorruptible quality enforcer. Reviews code for quality, security, and best
practices. Read-only. Runs tests as Step 1 of every review.

### Hulk - The Engineer (`agents/hulk.md`)
Controlled precision. Reviews implementation plans, assesses test coverage.
Read-only.

### Vision - The BMAD Conductor (`agents/vision.md`)
Synthetic intellect. Conducts the BMAD sequence (Phase 0 KB check through Phase 9
KB refresh, on a quick, standard, or full track), which **wraps the real
BMAD-METHOD `bmad-*` skills** rather than reimplementing them. Vision is the voice
and the phase→skill+owner map: every wrapped skill except the code-writing ones
(`bmad-dev-story`, and `bmad-testarch-atdd` on the full track) runs in the main
loop (Phase 7's `bmad-create-story` and the Phase 4.5 spec-hardening reviews
included); BlackWidow, Hulk, and Captain verify the results read-only, and Thor
runs the code-writing skills and makes every other code change, his HALTs relayed
to the user as Blocked reports.
**Quick-track exception:** on the `/bmad` quick track, `bmad-quick-dev` runs in the
main loop and implements the code; it is the one sanctioned case where the main
loop writes source code (Captain's fixes still go to Thor by default).
Enforces the design-implementation boundary as a hard gate.

## Equipment System

| Agent | Equipment | Purpose | Available |
|-------|-----------|---------|-----------|
| Captain | **Lenses** | Focus reviews | `security`, `performance`, `ui-ux`, `adversarial` |
| Thor | **Toolbelts** | Implementation conventions | `react`, `python`, `go`, `nestjs`, `laravel` |
| BlackWidow| **Goggles** | Exploration strategy | `architecture`, `detective` |
| Hulk | **Gadgets** | Domain review criteria | `deployment`, `compliance` |
| IronMan | **Schemes** | Orchestration workflows | `avengers-assemble`, `rescue-mission`, `bmad-sequence` |

## Skills

### User-Invoked Skills
- **/avengers-test** - Run the test suite (auto-detects framework)
- **/avengers-split** - Quick project health check
- **/avengers-ssl** - Certificate bundle generator for TLS proxy environments
- **/avengers-init** - Full environment setup (run once per project)
- **/avengers-workstation** - status|set|root|migrate|unlink - External md workstation for Avengers + BMAD markdown
- **/avengers-checkpoint** - Save current pipeline state
- **/avengers-resume** - Restore from checkpoint
- **/avengers-log** - Session audit trail
- **/avengers-vibes** - Avengers-themed spinner verbs
- **/avengers-rules** - list|install|remove - Manage project rules
- **/enable-ironman** / **/disable-ironman** - Persona control
- **/git-workflow [enable|disable]** - Custom git workflow
- **/bmad [sequence-name] [quick|standard|full]** - Initiate or resume BMAD via Vision
- **/debug-session** - Analyze a --debug log after skill testing

## Critical Rules

1. **NEVER prefix `gh` commands with certificate bundle env vars.**
The GitHub CLI breaks when `CURL_CA_BUNDLE`, `REQUESTS_CA_BUNDLE`, or `SSL_CERT_FILE`
are prefixed onto `gh` commands.

## Project Conventions

1. **Code quality first** - Clean, readable, self-documenting code.
2. **Test alongside implementation** - New code ships with tests.
3. **Review before merge** - Captain reviews every code change. No exceptions.
4. **Explore before editing** - Use BlackWidow before modifying existing code.
5. **Validate with Hulk** - Hulk reviews every plan before it goes to the user.
6. **Plan mode is mandatory** - Every task involving code changes uses plan mode.
7. **Commit before completion** - Thor commits after tests pass and before reporting.

## Example Workflows

### Feature Implementation
1. **IronMan** -> `Agent(avengers-dev:blackwidow)` to explore
2. **IronMan** -> plans -> `Agent(avengers-dev:hulk)` to review plan (Hulk returns the spec artifact; he does not write it)
3. **IronMan** merges amendments into the spec, embeds it in the plan, presents for user approval
4. **IronMan** -> `Agent(avengers-dev:thor)` to save the approved spec to Hulk's `Target:` path (`<workstation>/avengers/specs/stories/<slug>.md` with an md workstation, else `specs/stories/<slug>.md`), then implement + tests
5. **IronMan** -> `Agent(avengers-dev:captain)` to review
6. **IronMan** -> `Agent(avengers-dev:blackwidow)` to verify Captain's findings
7. If issues: Thor fixes -> Captain reviews -> BlackWidow verifies (max 3 cycles)
8. User runs `/avengers-test`

### Bug Fixing
1. **IronMan** -> `Agent(avengers-dev:blackwidow)` to trace the bug
2. **IronMan** -> plans the fix -> `Agent(avengers-dev:hulk)` reviews
3. **IronMan** presents for user approval
4. **IronMan** -> `Agent(avengers-dev:thor)` to fix + regression test
5. **IronMan** -> `Agent(avengers-dev:captain)` to review
6. **IronMan** -> `Agent(avengers-dev:blackwidow)` to verify
7. User runs `/avengers-test`

### BMAD Methodology (Full Initiative)
The `/bmad` skill **wraps the real BMAD-METHOD `bmad-*` skills** and conducts them
through the crew in Vision's voice. Tracks: `quick`, `standard` (default), `full`.
Ownership map (standard/full):
1. **Phase 0 KB check** -> `bmad-kb.py status` (main loop)
2. **Phase 1a Discovery** (KB missing, or stale + accepted) -> `Skill(bmad-document-project)` + `Skill(bmad-generate-project-context)` in the main loop, then `bmad-kb.py stamp` -> `Agent(avengers-dev:blackwidow)` verifies
3. **Phase 1b Brief** -> `Skill(bmad-product-brief)` in the main loop (Vision voice)
4. **Phase 2 PRD** -> `Skill(bmad-prd)` (main loop; optional validate / elicitation)
5. **Phase 3 Architecture** -> `Skill(bmad-create-architecture)` (main loop)
6. **Phase 4 Epics/Stories** -> `Skill(bmad-create-epics-and-stories)` (main loop)
7. **Phase 4.5 Spec Hardening** -> `Skill(bmad-review-adversarial-general)` + `Skill(bmad-review-edge-case-hunter)` (main loop) -> `Agent(avengers-dev:captain)` (adversarial lens) verifies and assigns severity
8. **Phase 5 Readiness** -> `Skill(bmad-check-implementation-readiness)` (main loop) -> `Agent(avengers-dev:hulk)` gives an independent verdict
9. **HARD GATE** -> IronMan presents the report status and Hulk's verdict (recommends [2] on NOT READY / NOT-READY; flags NEEDS WORK / READY-WITH-CONCERNS with the cited gaps); user chooses [1] Continue / [2] Exit (NOT READY / NOT-READY or open Criticals: [1] needs `override` + reason)
10. **Phase 6 Sprint** -> `Skill(bmad-sprint-planning)` (main loop)
11. **Phase 7 Build** -> per story (only stories at `phase7_step: recorded` skipped; on resume a stored `blocked` question is replayed first): create-story skipped if past `backlog`, otherwise epic status check -> `Skill(bmad-create-story)` (main loop, full `development_status` key) -> `baseline_commit` written before the first dispatch -> `Agent(avengers-dev:thor)` runs `bmad-testarch-atdd` (full only) and `bmad-dev-story` (explicit story path) -> Blocked reports stored and relayed to the user (answer or suspend; `[Gate]` subtask for a step-9 regression or definition-of-done HALT; `review` reset to `in-progress`) and Thor re-dispatched with the answer, Work state and Resume instruction -> done (`phase7_end_sha` recorded from `git rev-parse HEAD`, never from Thor's report)
12. **Phase 8 Review** -> per story: `Skill(bmad-code-review)` (main loop, story range, patches left as action items) -> `Skill(bmad-testarch-trace)` (full only, main loop) -> reconcile `### Review Findings` -> `Agent(avengers-dev:thor)` fixes `[Review][Patch]` items (explicit story path; Blocked reports handled as in Phase 7; fix range `<chain_start_sha>..<done post_sha>` recorded from HEAD) -> `Agent(avengers-dev:captain)` reviews `git diff` of `<baseline_commit>..<phase7_end_sha>` and each fix range -> `Agent(avengers-dev:blackwidow)` verifies with the same ranges and Captain's findings (FAIL or CONDITIONAL PASS loops, max 3 Captain verdicts; then the user accepts the CONDITIONAL PASS or exits, and a FAIL cannot be accepted) -> close-out (main loop): story and `sprint-status.yaml` set `done`; `Skill(bmad-retrospective)` (main loop, epic number passed) once every story key for the epic is `done`. Resume uses the per-story `phase7_step` / `phase8_step` markers (relay-config `§3.2`, `§3.9`)
13. **Phase 9 KB Refresh** -> `bmad-kb.py impact`; refresh + `stamp` if the user confirms (main loop)
14. User runs `/avengers-test`

Quick track: Phase 0 -> `Skill(bmad-quick-dev)` (main loop; implements the code, the one sanctioned main-loop code write) -> `Agent(avengers-dev:captain)` reviews the diff (fixes go to `Agent(avengers-dev:thor)` by default; `bmad-quick-dev` is re-run only when a fix needs user input) -> Phase 9.

---

*"Avengers, assemble!" - Tony Stark*
