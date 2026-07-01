# Adversarial Lens

## When to Equip

Use when reviewing specification documents - strategic briefs, ADRs, execution
specs - to find gaps, contradictions, missing edge cases, and unstated assumptions.

## Focus Areas

- [ ] Acceptance criteria present, concrete, and independently verifiable
- [ ] All actors and stakeholders explicitly named
- [ ] Success criteria are measurable, not subjective
- [ ] Scope boundaries stated for both in-scope and out-of-scope
- [ ] Error states and failure modes addressed, not just happy-path flows
- [ ] Edge cases: empty inputs, maximum volumes, concurrent access, clock skew
- [ ] Requirements are testable
- [ ] No conflicting requirements within the document
- [ ] Terminology is consistent throughout
- [ ] External dependencies named explicitly
- [ ] Decision rationale recorded

## Patterns to Flag

- Requirements using "should" or "may" where "must" is clearly intended
- Acceptance criteria requiring subjective judgment
- Missing error states for every described success flow
- Options analysis that lists only one option
- ADR consequences that list only upsides
- Requirements that reference undefined terms

## Reference

- IEEE 830: completeness, consistency, verifiability, unambiguity
- RFC 2119 keyword discipline: MUST / SHOULD / MAY
