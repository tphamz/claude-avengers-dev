# BMAD Sequence - Full Methodology Scheme

## When to Equip

Use when IronMan says "run BMAD", "start a BMAD sequence", or "use the BMAD
methodology" for a new initiative or sprint.

This scheme **wraps the real BMAD-METHOD `bmad-*` skills** and conducts them through
the crew in Vision's voice. It does not reimplement BMAD.

## The Crew — phase → real skill → owner → mode

| Phase | Real skill(s) | Owner | Mode |
| ----- | ------------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` / `bmad-investigate` | BlackWidow | autonomous |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |
| 2 PRD | `bmad-prd` | main loop (Vision voice) | interactive |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | Hulk | autonomous |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | light |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | Thor (per story) | autonomous |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | Captain | autonomous |

**Why the split:** the wrapped `bmad-*` skills are interactive (they ask the user
questions). A subagent runs blind and cannot elicit, so interactive phases run in
the main loop; only the non-interactive phases (whose real work belongs to a
specialist Avenger) are delegated.

## Design-Implementation Boundary

After Phase 5, Hulk reports the readiness verdict and the relay halts. IronMan
presents it to the user for an explicit choice — **[1] Continue into implementation
/ [2] Exit** — before Phase 6 begins. No auto-advance.

## Artifacts

Written by the wrapped `bmad-*` skills, under their own conventions (BMAD-METHOD
typically writes to `docs/`). The relay's own state file:
`.avengers/relay-sequences/bmad-{name}.yaml`.

## Completion Criteria
- [ ] All phases completed (1a → 8)
- [ ] Design-implementation hard gate cleared with explicit user authorization
- [ ] All stories built (Thor) and reviewed (Captain)
- [ ] Captain verdict: PASS or CONDITIONAL PASS (max 3 review cycles, else escalate)
- [ ] State file transitioned to `complete`
