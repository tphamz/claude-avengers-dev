# Avengers Assemble - Feature Implementation Scheme

## When to Equip

Use for standard feature implementation. IronMan's default scheme for new functionality.

## The Crew

| Phase        | Agent      | Equipment                | Task                    |
| ------------ | ---------- | ------------------------ | ----------------------- |
| Recon        | BlackWidow | architecture goggles     | Explore the target area |
| Blueprint    | Hulk       | deployment gadget        | Review the plan         |
| Execution    | Thor       | project toolbelt         | Build the feature       |
| Inspection   | Captain    | concern-appropriate lens | Review the code         |
| Verification | BlackWidow | detective goggles        | Verify review findings  |

## Phase 1: Recon

Dispatch BlackWidow to explore the codebase area.
Equip: architecture goggles for multi-module features, detective goggles for complex existing logic.

## Phase 2: Blueprint

Draft the implementation plan based on BlackWidow's findings.
Dispatch Hulk to review. Present to user for approval.
Equip: deployment gadget if the feature involves infrastructure changes.

## Phase 3: Execution

Dispatch Thor to implement and write tests.
Equip: project-appropriate toolbelt (react, python, go, nestjs, laravel) if one matches.

## Phase 4: Inspection

Dispatch Captain to review Thor's changes.
Equip: security lens for auth/user data. Performance lens for data-heavy paths.

## Phase 5: Verification

Dispatch BlackWidow to verify Captain's findings for false positives.
If issues remain: Thor fixes -> Captain reviews -> BlackWidow verifies. Max 3 cycles.

## Completion Criteria

- [ ] Feature implemented per plan
- [ ] Tests passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS with no Critical findings
- [ ] Code committed
