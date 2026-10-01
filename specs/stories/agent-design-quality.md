# Agents: design-quality criteria for Captain, Hulk and Thor

## Objective
Give Captain a code-review rubric that covers design smells and over-engineering, give
Hulk a plan-review rubric for structure, design and extensibility, and have Thor design
before coding and self-review before committing. One shared design standard binds all
three, and the toolbelts gain a default folder layout.

## Scope

**Files to Create/Modify/Delete**
- `agents/captain.md` — `## Review Criteria` after the report template (code reviews only; Hardening Verification and `/sdd` verify keep their own; lenses add to it); severity rules; Warning row
- `agents/hulk.md` — `## Plan Review Criteria` (structure, design, extensibility; gadgets add to it); `**Design & Structure**:` report line; `## Design` in the spec template
- `agents/thor.md` — "Design before code" step with the design-conflict stop (generic Blocked Report, `Skill: n/a (design conflict)`); inline "Self-review" checklist; `**Design Notes**:` report field; step reference renumbered
- `personas/ironman.md` — `## Design & Structure` after `## Approach` in the Plan Template
- `equipment/toolbelts/{python,react,nestjs,laravel}.md` — `## Folder Structure` in go.md's bullet format, for projects with no established layout; one Patterns to Avoid item for long type-switch chains
- `tests/test_doc_consistency.py` — the shared design standard is byte-identical in captain.md, hulk.md and thor.md, plus a mutation test
- `specs/stories/agent-design-quality.md` — this spec

## Design
Documentation change in the existing agent and toolbelt formats: each new section follows its
file's section order and heading level, and the toolbelt sections copy `go.md`. The shared rule
is one bold-led paragraph copied into three files; the new checker follows the module's pure
checker plus real-file test plus mutation test pattern.

## Acceptance Criteria
- [ ] The "Design standard" paragraph is byte-identical in captain.md, hulk.md and thor.md, and a test enforces it
- [ ] Captain's design smells are `[WARNING]` only when concrete and cited; speculative abstraction is `[WARNING]`; naming is `[SUGGESTION]`/`[NIT]`; `[CRITICAL]` is unchanged
- [ ] Thor's self-review checklist is inline and does not reference captain.md
- [ ] A design conflict stops Thor with the generic Blocked Report and no commit; minor deviations go in `**Deviation from Plan**`
- [ ] Toolbelt Folder Structure sections use go.md's `` - `dir/`: purpose `` format; go.md is unchanged
- [ ] No Part A files touched (references/bmad, skills/bmad, agents/vision.md, bmad-sequence.md)
- [ ] `python3 -m unittest discover -s tests` passes

## Tasks
- [ ] Edit captain.md, hulk.md, thor.md and the persona Plan Template
- [ ] Add Folder Structure and the type-switch item to the four toolbelts
- [ ] Add the byte-identity checker and tests
- [ ] Run the tests and commit `feat(agents): design-quality criteria for Captain, Hulk and Thor`; do not push

## Engineering Notes (Hulk)
- Thor cannot read captain.md in target projects, so his checklist must be inline.
- Warning severity is limited to concrete, cited smells, so reviews do not stall on taste.
- The design-conflict stop reuses the Blocked Report rather than adding a new template.
- go.md keeps no type-switch item: type switches are idiomatic Go.

## Status
- [x] Spec approved by user
