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
| 1a Discovery (if KB missing / stale + accepted) | `bmad-document-project` + `bmad-generate-project-context` → `stamp` | main loop (Vision voice) | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` (+ optional validate / elicitation) | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | Captain (`adversarial` lens) | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | Hulk | standard, full |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full) → `bmad-dev-story` | Thor (per story) | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full) + `bmad-retrospective` | Captain | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → refresh if confirmed → `stamp` | main loop (Vision voice) | all |

**Why the split:** the wrapped `bmad-*` skills are interactive (they ask the user
questions). A subagent runs blind and cannot elicit, so interactive phases run in
the main loop; only the non-interactive phases (whose real work belongs to a
specialist Avenger) are delegated.

## Design-Implementation Boundary

After Phase 5, Hulk reports the readiness verdict and the relay halts. IronMan
presents it to the user for an explicit choice — **[1] Continue into implementation
/ [2] Exit** — before Phase 6 begins. No auto-advance. If readiness is FAIL or
Phase 4.5 Criticals are unresolved, [1] needs `override` plus a reason.

## Artifacts

Written by the wrapped `bmad-*` skills, under their own conventions (BMAD-METHOD
typically writes to `docs/`). The relay's own state file:
`.avengers/relay-sequences/bmad-{name}.yaml`.

## Completion Criteria
- [ ] All phases for the chosen track completed (Phase 0 through Phase 9)
- [ ] Design-implementation hard gate cleared with explicit user authorization
      (any override recorded with a reason)
- [ ] All stories built (Thor) and reviewed (Captain)
- [ ] Captain verdict: PASS or CONDITIONAL PASS (max 3 review cycles, else escalate)
- [ ] Phase 9 KB refresh evaluated (refreshed and stamped, or not needed)
- [ ] State file transitioned to `complete`
