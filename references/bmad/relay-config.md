# BMAD Methodology Relay - Configuration

This is the configuration and protocol reference for the BMAD relay methodology.
Vision loads this at relay start to understand operational parameters.

## Relay Identity

- **Name:** BMAD (Build More Architect Dreams)
- **Type:** methodology-relay
- **Phases:** 8 (linear 1-5, iterative 6-8)
- **Orchestrator:** Vision agent

## Phase Map

| Phase | Name              | Type      | Key Artifact                          |
|-------|-------------------|-----------|---------------------------------------|
| 1     | Assessment        | Linear    | Auto-assessment + Product Brief       |
| 2     | Requirements      | Linear    | TRD + PRD                             |
| 3     | Technical Design  | Linear    | TDD + ADRs + Test Strategy            |
| 4     | Planning          | Linear    | Implementation Plan + Backlog + Stories |
| 5     | Delivery Readiness| Linear    | Delivery Readiness Report             |
| 6     | Sprint Planning   | Linear    | sprint-status.yaml                    |
| 7     | Story Implementation | Iterative | Code + story updates                |
| 8     | Review & Completion | Linear  | Code review + sprint completion       |

## State File

Location: `.avengers/relay-sequences/bmad-{name}.yaml`

### State Schema

```yaml
sequence_id: string           # Unique identifier: bmad-{name}
name: string                  # Human name: {name}
status: enum                  # active | suspended | complete | closed | abandoned
current_phase: int            # 1-8
design_implementation_boundary_passed: bool  # Phase 5->6 hard gate
created_at: timestamp
last_active: timestamp

relay_modifiers:
  existing_code_in_scope: bool   # Brownfield mode
  depth_level: enum              # lightweight | standard | enterprise (v1.1)

artifacts:
  auto_assessment: string        # File path
  product_brief: string
  project_context: string        # Brownfield only
  trd: string
  prd: string
  tdd: string
  adrs: string
  test_strategy: string
  implementation_plan: string
  product_backlog: string
  dev_stories: string            # Directory path
  delivery_readiness: string
  sprint_status: string

loop_state:                      # Phase 7 only
  total_items: int
  completed: list
  in_progress: string | null
  remaining: list
  in_progress_state: object | null
```

## Protocol Directives

### §2.2 Close-Out Dialogue

When user says 'stop' during any phase:
1. Save current state to disk
2. Ask: "Save and suspend (resume later) or close out permanently?"
3. `suspended` = paused, resume available
4. `closed` = user is done; artifacts preserved but relay inactive

### §2.5 No Role-Play

Operate as Vision's functional persona — do not role-play as human characters.
Expertise overlays draw on human references for capability framing only.

### §2.7 Deterministic-First

When a check can be expressed as grep, file existence, count, or regex — use that
operation rather than LLM judgment. LLM judgment is surfaced as advisory, not blocking.

### §3.2 Resume Protocol

On resume, read state file first. Surface to user:
> "Resuming BMAD '{name}' at Phase {N}: {phase-name} ({context})."

### §3.3 Artifact-Reset Policy

Each phase loads prior artifacts fresh from disk. Recommended: `/clear` between phases
for strict context isolation. `context_policy: artifact-reset` is authoritative.

### §3.4 Iterative Phase Batching

Phase 7 supports per-story review stops. User may batch approvals with "approve the next N".
Auto-clears batch on scope creep detection per §3.7.

### §3.5 Phase Boundary Confirmation

Each phase announces completion and waits for user confirmation before advancing.
Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"

### §3.6 Design-Implementation Boundary (Hard Gate)

The boundary between Phase 5 and Phase 6 is a hard gate. User must explicitly choose:
- [1] Continue into implementation
- [2] Exit (artifacts saved, relay suspended)

No auto-advance. No batch-through.

### §3.7 Scope Creep Prevention

During Phase 7, if implementation surfaces out-of-scope requirements:
- Surface to user with three options (note/defer, pause-replan, add-informally)
- Auto-clear any active batch
- Do not implement out-of-scope items silently

### §5 One-Phase-At-A-Time Loading

Vision loads phase persona overlays one at a time from `references/bmad/phase-N-*.md`.
Do not load all 8 phases at once. Load the current phase overlay; clear on advance.

## Artifact Paths

All artifacts write to `docs/planning/` by default:

```
docs/planning/
  planning_phase1_auto-assessment.md
  planning_phase1_product-brief.md
  planning_phase2_trd_requirements.md
  planning_phase2_prd_requirements.md
  planning_phase3_tdd_technical-design.md
  planning_phase3_adr_decisions.md
  planning_phase3_test-strategy.md
  planning_phase4_implementation-plan.md
  planning_phase4_product-backlog.md
  planning_phase4_dev-stories/
    {epic}-{story}-{slug}.md
  planning_phase5_delivery-readiness.md
  sprint-status.yaml
  retrospectives/
    sprint-{N}-retro.md
```

Variable `{base_path}` = `docs/planning` throughout phase files.
