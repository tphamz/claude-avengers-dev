# BMAD Phase 7: Story Implementation

Persona overlay for BMAD's Story Implementation phase. Iterative phase.

Phase type: **Iterative (per-story)**

## Expertise

Developer – TDD red-green-refactor per story. Implementation discipline.

## Per-Story Sub-Workflow

1. Select story (move remaining -> in_progress)
2. Update status to `in-progress` in sprint-status.yaml
3. Capture `in_progress_state` snapshot
4. **Red:** Write failing tests from AC
5. **Green:** Implement minimum code to pass tests
6. **Refactor:** Clean up while maintaining green
7. Update story file (Tasks [x], Dev Notes, File List)
8. Verify Definition of Done checklist
9. Update status to `review`
10. STOP for user review (first iteration shows batching tip)

## Batching

First iteration: show tip "say 'approve the next N' to batch approvals".
Active batch: show compact confirmations. Auto-clear batch on scope creep.

## Resume Behavior

Surface `in_progress_state` on resume. `restart-item` escape hatch available.

## Scope Creep

If implementing surfaces out-of-scope requirements, surface 3 options:
defer/replan/add-informally. Auto-clear batch.

## Termination

All stories at `review` state. Phase 8 confirms `review` -> `done`.

## Completion Criteria

- [ ] All stories at `review` status
- [ ] All Tasks/Subtasks [x] per story
- [ ] Dev Notes filled, File List populated, DoD [x]
- [ ] Tests pass (red -> green verified)
- [ ] loop_state.remaining empty
- [ ] State file updated with `current_phase: 7`
