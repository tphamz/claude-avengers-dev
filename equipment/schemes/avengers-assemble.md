# Avengers Assemble - Feature Implementation Scheme

## When to Equip

Use for standard feature implementation. IronMan's default scheme for new functionality.

## The Crew

| Phase                 | Agent      | Equipment                | Task                                    |
| --------------------- | ---------- | ------------------------ | --------------------------------------- |
| Recon                 | BlackWidow | architecture goggles     | Explore the target area                 |
| Blueprint             | Hulk       | deployment gadget        | Review the plan                         |
| Execution             | Thor       | project toolbelt         | Build the feature                       |
| Inspection            | Captain    | concern-appropriate lens | Review the code                         |
| Verification          | BlackWidow | detective goggles        | Verify review findings                  |
| KB Sync (conditional) | IronMan    | -                        | Impact check; refresh KB if user agrees |

## Phase 1: Recon

KB Sync start: if `_bmad/` and `.avengers/kb.json` both exist, run
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py status` and record `head` as
`<start-sha>` and `state` as `<kb-state-at-start>`. Skip KB Sync silently if either path is
missing, `status` exits 1, `head` is null, or `state` is `unknown`. If `state` is `missing`,
skip with the note "run /bmad to build the KB". If `status` warns on stderr that `kb.json`
was malformed (it is backed up to `kb.json.bak`), mention it and skip.

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

## Phase 6: KB Sync

Conditional: runs only if the Phase 1 KB Sync start check did not skip. Runs once,
after the final fix cycle of Phase 5 and after "Code committed" holds.
If paths outside the KB docs are uncommitted, report "KB Sync deferred: uncommitted
changes" and stop.

Base: `<start-sha>` if `<kb-state-at-start>` was `fresh`; otherwise the `commit` in
`.avengers/kb.json`, so drift from before this scheme is included and the stamp stays
honest. If `<start-sha>` was lost (e.g. after compaction), use the `kb.json` commit.
If that is absent too, skip with a note.

Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py impact --base <base>` and
branch on the exit code, not the JSON: exit 2 -> nothing to sync. Exit 1 -> note the
error and skip. Exit 0 with `refresh_recommended: false` -> nothing to sync. Exit 0 with
`refresh_recommended: true` -> show `signals` (type: detail) and `changed_areas`, then
ask the user whether to refresh the KB as a plain chat question (not a structured
question tool).

On yes: follow steps 2-5 of `${CLAUDE_PLUGIN_ROOT}/references/bmad/phase-9-kb-refresh.md`
in the main loop: `bmad-document-project` in `deep_dive` once per changed area (or
`full_rescan` if more than 3 areas), then `bmad-generate-project-context`. Adaptation:
use `<base>` wherever the reference says `kb_base_commit`; ignore every relay-state
instruction (`status`, `complete`, `current_phase`) and the Resume defaults paragraph;
speak as IronMan. These skills run in the main loop because they ask the user
questions (`references/bmad/relay-config.md` §3.10); this is the one carve-out from
Agent() delegation.

Dispatch Thor to commit the refreshed KB docs (`docs: refresh project KB`). They are
generated docs, not code, so Captain review is not required. Then run
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py stamp`: exit 0 -> stamped. Exit
2 -> already stamped at HEAD, OK. Exit 1 -> report "KB refreshed but not stamped".

On no: record "KB refresh declined" in the final report.

`${CLAUDE_PLUGIN_ROOT}` is the plugin directory this scheme was loaded from; substitute
the absolute path if the variable is not set in the shell.

## Completion Criteria

- [ ] Feature implemented per plan
- [ ] Tests passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS with no Critical findings
- [ ] Code committed
- [ ] KB refreshed if impact flagged
