# SDD Verify — Captain's Procedure

<!--
Adapted from OpenSpec 1.13.2's `openspec-verify-change` workflow template
(dist/core/templates/workflows/verify-change.js in @fission-ai/openspec,
https://github.com/Fission-AI/OpenSpec). Copyright (c) 2024 OpenSpec Contributors,
used under the MIT License (the license text is reproduced in
references/sdd/schemas/avengers-sdd/schema.yaml).

Changes: change selection, store handling and the /opsx:verify naming are removed
(the relay passes one change); the evidence comes from the change files and
`sdd-openspec.py instructions apply`; the standard track adds a tests-first check;
the result feeds Captain's review verdict. Re-check against upstream when the pinned
OpenSpec version (1.13.2) changes.
-->

Captain runs this in Phase V of `/sdd`, alongside the normal code review of the
diff. It is read-only: never implement tasks, edit artifacts, or archive.

## Inputs (from the dispatch prompt)

- the change id and the `sdd-openspec.py status` JSON — `change_dir_real`,
  `schema`, `artifacts`, `tasks_done`, `tasks_total`
- the track (`quick` or `standard`)
- the commit range or diff Thor produced

## Steps

1. **Load the artifacts.** Read everything under `change_dir_real`: `proposal.md`,
   `specs/**/spec.md` (the delta specs), `design.md`, `tasks.md`, and on the
   standard track `tests.md`. For task progress run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd-openspec.py instructions apply <change>`
   (exit 0: JSON with `contextFiles`, `tasks`, `progress`, `taskTrackingConfigured`;
   exit 1: note it and use `tasks.md` directly). Treat its `state` and `instruction`
   as context, not a verdict.

2. **Set up the report** with three dimensions — **Completeness**, **Correctness**,
   **Coherence** — each holding CRITICAL, WARNING or SUGGESTION issues.
   Respect intentional omissions (`skip_specs: true`, no `design.md`): mark those
   checks **Not applicable**, never invent the artifact. Reserve **Not verified**
   for applicable checks whose evidence is missing or unreadable, and say why.

3. **Completeness.**
   - **Task Completion:** report done vs total from `progress` (or `tasks.md`). Each
     incomplete task is a CRITICAL: "Complete task: <description>" or "Mark as done
     if already implemented".
   - **Spec Coverage:** list every requirement in the delta specs with its section
     (`## ADDED`, `## MODIFIED`, `## REMOVED`, `## RENAMED Requirements`).
     - ADDED / MODIFIED (check the delta's text): search the code for it. Not found
       → CRITICAL "Requirement not found: <name>".
     - REMOVED: invert the check. Code that still delivers the removed behavior →
       CRITICAL "Removed requirement still implemented: <name>". Finding nothing is
       the expected result; matches in `openspec/` or docs are not evidence.
     - RENAMED (`FROM:`/`TO:`): behavior is unchanged. Check the TO requirement's
       behavior against the baseline in `openspec/specs/<capability>/spec.md`; do
       not require renamed symbols. Missing → CRITICAL "Renamed requirement not
       found: <TO name>". A baseline that cannot be read is Not verified.

4. **Correctness.** A change whose deltas only remove or rename requirements marks
   both checks below Not applicable.
   - **Requirement Implementation Mapping:** for each ADDED / MODIFIED requirement,
     note the implementing `file:line` ranges. Divergence → WARNING "Implementation
     may diverge from spec: <details>".
   - **Scenario Coverage:** for each `#### Scenario:` under an ADDED / MODIFIED
     requirement, check the code handles it and a test covers it. Uncovered →
     WARNING "Scenario not covered: <scenario>".
   - **Tests first (standard track only):** every scenario must map to a test listed
     in `tests.md`, and that test must exist and pass. Run the `## Run` command from
     `tests.md`. A scenario with no test, a listed test that is missing, or a
     failing test → CRITICAL. A `## Not automated` entry is a WARNING unless its
     stated alternative verification was done.

5. **Coherence.**
   - **Design Adherence:** check the key decisions in `design.md` are followed.
     Contradiction → WARNING "Design decision not followed: <decision>".
   - **Code Pattern Consistency:** new code against the project's patterns (naming,
     layout, style). Significant deviation → SUGGESTION.

6. **Report.**

   ```markdown
   ## Verification Report: <change>

   | Dimension    | Status              |
   |--------------|---------------------|
   | Completeness | X/Y tasks, N reqs   |
   | Correctness  | M/N reqs covered    |
   | Coherence    | Followed / Issues   |
   ```

   In each cell report the checks that ran and `Not verified (<reason>)` for each
   skipped one; never score a skipped check as passing. Count only ADDED and
   MODIFIED requirements in N; report removals and renames separately.

   Then the issues by priority — CRITICAL (fix before archive), WARNING (should
   fix), SUGGESTION (nice to fix) — each with a specific recommendation and
   `file:line` references.

## Heuristics

- Completeness: objective items (checkboxes, requirement lists).
- Correctness: keyword search, file paths, reasonable inference; perfect certainty
  is not required.
- Coherence: glaring inconsistencies, not style nitpicks.
- When uncertain, prefer SUGGESTION over WARNING and WARNING over CRITICAL.

## Mapping to Captain's verdict

The verify findings join the code-review findings under Captain's normal tags:
CRITICAL → `[CRITICAL]`, WARNING → `[WARNING]`, SUGGESTION → `[SUGGESTION]`. Any
Not verified check is listed in the verdict with its reason. The relay advances to
archive only on PASS, or CONDITIONAL PASS with no `[CRITICAL]` (the `/bmad` quick
track rule).
