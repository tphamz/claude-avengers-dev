# BMAD Sequence - Full Methodology Scheme

## When to Equip

Use when IronMan says "run BMAD", "start a BMAD sequence", or "use the BMAD
methodology" for a new initiative or sprint.

## The Crew

| Phase               | Agent            | Task                                       |
| ------------------- | ---------------- | ------------------------------------------ |
| 1-5 (Design)        | Vision           | Assessment through Delivery Readiness      |
| 6 (Sprint Planning) | Vision           | Sprint setup, story assignment             |
| 7 (Story Impl.)     | Thor (per story) | Implement each story + write all artifacts |
| 8 (Review)          | Captain          | Code review + DoD validation               |

## Design-Implementation Boundary

After Phase 5, Vision halts and surfaces the Delivery Readiness Report.
IronMan presents it to the user for explicit approval before Phase 6 begins.

## Story State Machine

```
backlog -> ready-for-dev -> in-progress -> review -> done
```

## Artifact Paths (written to `docs/planning/`)
- `planning_phase1_auto-assessment.md`
- `planning_phase1_product-brief.md`
- `planning_phase2_trd_requirements.md`
- `planning_phase2_prd_requirements.md`
- `planning_phase3_tdd_technical-design.md`
- `planning_phase3_adr_decisions.md`
- `planning_phase3_test-strategy.md`
- `planning_phase4_implementation-plan.md`
- `planning_phase4_product-backlog.md`
- `planning_phase4_dev-stories/` (directory of story files)
- `planning_phase5_delivery-readiness.md`
- `sprint-status.yaml`

State file: `.avengers/relay-sequences/bmad-{name}.yaml`

## Completion Criteria
- [ ] All 8 phases completed
- [ ] All stories status = done
- [ ] Captain verdict: PASS or CONDITIONAL PASS
- [ ] All artifacts committed to docs/planning/
