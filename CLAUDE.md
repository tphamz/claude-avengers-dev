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

### Vision - The BMAD Orchestrator (`agents/vision.md`)
Synthetic intellect. Runs the full 8-phase Build More Architect Dreams methodology.
Dispatches Thor (Phase 7) and Captain (Phase 8).
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
- **/avengers-checkpoint** - Save current pipeline state
- **/avengers-resume** - Restore from checkpoint
- **/avengers-log** - Session audit trail
- **/avengers-vibes** - Avengers-themed spinner verbs
- **/avengers-rules** - list|install|remove - Manage project rules
- **/enable-ironman** / **/disable-ironman** - Persona control
- **/git-workflow [enable|disable]** - Custom git workflow
- **/bmad [sequence-name]** - Initiate or resume BMAD via Vision
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
1. **IronMan** -> `Agent(blackwidow)` to explore
2. **IronMan** -> plans -> `Agent(hulk)` to review plan
3. **IronMan** amends, presents for user approval
4. **IronMan** -> `Agent(thor)` to implement + tests
5. **IronMan** -> `Agent(captain)` to review
6. **IronMan** -> `Agent(blackwidow)` to verify Captain's findings
7. If issues: Thor fixes -> Captain reviews -> BlackWidow verifies (max 3 cycles)
8. User runs `/avengers-test`

### Bug Fixing
1. **IronMan** -> `Agent(blackwidow)` to trace the bug
2. **IronMan** -> plans the fix -> `Agent(hulk)` reviews
3. **IronMan** presents for user approval
4. **IronMan** -> `Agent(thor)` to fix + regression test
5. **IronMan** -> `Agent(captain)` to review
6. **IronMan** -> `Agent(blackwidow)` to verify
7. User runs `/avengers-test`

### BMAD Methodology (Full Initiative)
1. **IronMan** -> `Agent(vision)` to run BMAD Phase 1-5
2. **Vision** produces: assessment, brief, PRD, TDD, ADRs, test strategy, impl plan,
   backlog, dev stories, delivery readiness report
3. **Vision** surfaces Delivery Readiness; IronMan presents for design-implementation authorization
4. After authorization: Vision runs Phase 6 (Sprint Planning)
5. **Vision** -> `Agent(thor)` in Phase 7
6. **Vision** -> `Agent(captain)` in Phase 8
7. User runs `/avengers-test`

---

*"Avengers, assemble!" - Tony Stark*
