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

KB Sync start (IronMan, before dispatching BlackWidow): if `_bmad/` and `.avengers/kb.json`
both exist, run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py status` and
record `head` as `<start-sha>`, `state` as `<kb-state-at-start>`, the parent directories of
`index_path` and `context_path` as `<kb-dir>` and `<output-dir>`, and whether `signals`
contains an `unknown_stamp` entry (keep its `detail`). Skip KB Sync silently if either path
is missing, `status` exits 1, `head` is null, or `state` is `unknown`. If `state` is
`missing`, skip with the note "run /bmad to build the KB". If `status` warns on stderr that
`kb.json` was malformed (it is backed up to `kb.json.bak`), mention it and skip.

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

Deferral: from the project dir, run
`git status --porcelain -z --untracked-files=no -- .` (NUL-separated, so names are not
quoted; `-- .` scopes it to the project; untracked files are ignored). Paths are
repo-root-relative: strip the `git rev-parse --show-prefix` prefix, then compare to the
project-relative `.avengers/`, `_bmad/`, `<kb-dir>/` and `<output-dir>/`. If any path is
outside them, report "KB Sync deferred: uncommitted changes" and stop. If `<kb-dir>` or
`<output-dir>` is the project root (`.` or empty), do not exclude the root: any tracked
modification defers.

Unknown stamp: if the start `status` reported an `unknown_stamp` signal, skip `impact`.
Show the signal's `detail` as the reason, ask the user whether to run a `full_rescan`
refresh, and on yes go to Refresh with `full_rescan`.

Base: `<start-sha>` if `<kb-state-at-start>` was `fresh`; otherwise the `commit` in
`.avengers/kb.json`, so drift from before this scheme is included and the stamp stays
honest. If `<start-sha>` was lost (e.g. after compaction), use the `kb.json` commit.
If that is absent too, skip with a note. If `<kb-dir>`, `<output-dir>` or the
`unknown_stamp` flag was lost, re-derive them by re-running `status`.

Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py impact --base <base>` and
branch on the exit code, not the JSON: exit 2 -> nothing to sync. Exit 1 -> note the
error and skip. Exit 0 with `refresh_recommended: false` -> nothing to sync. Exit 0 with
`refresh_recommended: true` -> show `signals` (type: detail) and `changed_areas`, then
ask the user whether to refresh the KB as a plain chat question (not a structured
question tool).

Refresh (on yes): follow steps 3-4 of
`${CLAUDE_PLUGIN_ROOT}/references/bmad/phase-9-kb-refresh.md` in the main loop:
`bmad-document-project` in `deep_dive` once per changed area, or `full_rescan` if there
are more than 3 areas or `changed_areas` is empty or contains `.`; then
`bmad-generate-project-context`. The ask above and the stamp below replace the
reference's other steps. Adaptation: use `<base>` wherever the reference says
`kb_base_commit`; ignore every relay-state instruction (`status`, `complete`,
`current_phase`) and the Resume defaults paragraph; speak as IronMan. These skills run
in the main loop because they ask the user questions; this is a carve-out from Agent()
delegation, as in the /bmad relay
(`${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md` §3.10).

Stamp, then commit:

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py stamp` first: exit
   0 -> stamped. Exit 2 -> already stamped at HEAD, OK. Exit 1 -> report "KB refreshed
   but not stamped" and still commit the docs.
2. Dispatch Thor to commit the refreshed KB docs plus `.avengers/kb.json` (if tracked)
   in one commit, `docs: refresh project KB`. The commit touches only `<kb-dir>`,
   `<output-dir>` and `.avengers/kb.json`; if either dir is the project root, list only
   the generated files (index path, generated docs, `context_path`, `.avengers/kb.json`),
   never the whole root. Never amend it after stamping. The KB stays
   fresh because `status` computes signals over stamped..HEAD and excludes those paths.
   The commit is generated documentation, not a code change, so Captain review is not
   required. If Thor's commit fails, report "KB stamped but docs not committed".

On no: record "KB refresh declined" in the final report.

Record `<start-sha>` in the final report for traceability.

`${CLAUDE_PLUGIN_ROOT}` is the plugin directory this scheme was loaded from; substitute
the absolute path if the variable is not set in the shell.

## Completion Criteria

- [ ] Feature implemented per plan
- [ ] Tests passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS with no Critical findings
- [ ] Code committed
- [ ] KB refreshed if impact flagged (outcome recorded: refreshed / declined / deferred / skipped)
