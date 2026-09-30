# Rescue Mission - Incident Response Scheme

## When to Equip

Use for bug fixes, incident response, and production issues. Optimized for
fast root-cause analysis and minimal blast radius.

## The Crew

| Phase                 | Agent      | Equipment                     | Task                                    |
| --------------------- | ---------- | ----------------------------- | --------------------------------------- |
| Triage                | BlackWidow | detective goggles             | Trace the bug, find root cause          |
| Assessment            | Hulk       | deployment gadget             | Review the fix plan                     |
| Surgery               | Thor       | project toolbelt              | Implement the fix                       |
| Verification          | Captain    | security lens (if applicable) | Review the fix                          |
| Confirmation          | BlackWidow | detective goggles             | Verify fix and findings                 |
| KB Sync (conditional) | IronMan    | -                             | Impact check; refresh KB if user agrees |

## Phase 1: Triage

KB Sync start (IronMan, before dispatching BlackWidow): if `_bmad/` exists, run
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py status`. Skip KB Sync
silently if it exits 1, `head` is null, or `state` is `unknown`. If `state` is `missing`,
skip with the note "run /bmad to build the KB". Then skip silently if `stamped_commit` is
null (if stderr warns the marker was malformed and backed up to `kb.json.bak`, mention it).
Otherwise record `head` as `<start-sha>`, `state` as `<kb-state-at-start>`,
`stamped_commit`, `workstation`, and any `unknown_stamp` or `branch_unstamped` signal (keep
its `detail`). A detached HEAD (key `HEAD@<sha7>`) normally has no entry of its own, so it
falls back to another branch's stamp (`branch_unstamped`). Derive the **in-repo KB dirs**
from `index_path` and `context_path`: with `workstation` null, the parent of each relative
path; with a workstation, only paths starting with `{project-root}/` (strip that prefix,
take the parent). Workstation-relative and absolute paths are outside the repo: never
an exclusion and never in the repo commit.

Dispatch BlackWidow with detective goggles.
Mission: trace data flow to root cause, assess blast radius, suggest fix approach.

## Phase 2: Assessment

Draft fix plan from BlackWidow's findings. Dispatch Hulk to review.
Present to user. For urgent issues, keep the plan concise.

## Phase 3: Surgery

Dispatch Thor to implement the minimal fix.
Write a regression test that reproduces the original bug.
Verify it fails without the fix and passes with it.

## Phase 4: Verification

Dispatch Captain to review.
Equip: security lens if the bug is security-related.

## Phase 5: Confirmation

Dispatch BlackWidow to verify Captain's findings.
If issues remain, loop max 3 cycles.

## Phase 6: KB Sync

Conditional: runs only if the Phase 1 KB Sync start check did not skip. Runs once,
after the final fix cycle of Phase 5 and after "Code committed" holds. Read the KB
marker only through `bmad-kb.py status`, never by path (relay-config §3.8).

Deferral: from the project dir, run
`git status --porcelain -z --untracked-files=no -- .` (NUL-separated, so names are not
quoted; `-- .` scopes it to the project; untracked files, including the `_bmad-output`
symlink, are ignored). An `R` or `C` entry is followed by a second NUL-separated field
(the original path, no status prefix); check both paths. Paths are repo-root-relative:
strip the `git rev-parse --show-prefix` prefix, then compare to the project-relative
`.avengers/`, `_bmad/` and each in-repo KB dir. If any path is outside them, report "KB
Sync deferred: uncommitted changes" and stop. If an in-repo KB dir is the project root
(`.` or empty), do not exclude the root: any tracked modification outside `.avengers/`
and `_bmad/` defers.

Unknown stamp: if the start `status` reported an `unknown_stamp` signal, skip `impact`.
Show the signal's `detail` as the reason, ask the user whether to run a `full_rescan`
refresh, and on yes go to Refresh with `full_rescan`.

Other-branch stamp: if it reported `branch_unstamped`, show its `detail`; the base is
that branch's `stamped_commit`, which the docs describe. Never report "nothing to sync"
here. If `git merge-base --is-ancestor <stamped_commit> HEAD` fails, handle it as an
unknown stamp and skip `impact`. Otherwise (ancestor check passed), run `impact` below:
if it exits 1, handle it as an unknown stamp; if it exits 2, or exits 0 with
`refresh_recommended: false`, the docs already describe HEAD: skip the refresh and ask
only whether to stamp, so this branch gets its own entry; on yes go to Stamp, then
commit.

Base: `<start-sha>` if `<kb-state-at-start>` was `fresh`; otherwise the recorded
`stamped_commit`, so drift from before this scheme is included and the stamp stays
honest. If any recorded value was lost (e.g. after compaction), re-run `status` and
re-derive it; if `stamped_commit` is null, skip with a note.

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
`bmad-generate-project-context`. The ask above and the stamp and commits below replace
the reference's other steps. Adaptation: use `<base>` wherever the reference says
`kb_base_commit`; ignore every relay-state instruction (`status`, `complete`,
`current_phase`) and the Resume defaults paragraph; speak as IronMan. These skills run
in the main loop because they ask the user questions; this is a carve-out from Agent()
delegation, as in the /bmad relay
(`${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md` §3.10).

Stamp, then commit:

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py stamp` first: exit
   0 -> stamped. Exit 2 -> already stamped at HEAD, OK. Exit 1 -> stamp reported an
   error; re-run `status` to confirm whether the marker was written (treat as stamped
   only if `stamped_commit` equals HEAD and it reports no `branch_unstamped` signal,
   since a fallback `stamped_commit` comes from another branch; otherwise report "KB
   refreshed but not stamped"), and still do the repo commit. Its other output is
   informational, e.g. `Refreshed .claude/rules/avengers-kb.md`.
2. Repo commit: from the project dir, if there are in-repo KB dirs, list candidates with
   `git status --porcelain -z --untracked-files=all -- <in-repo KB dirs>`, so new docs
   are included; if there are none, skip this listing entirely (an empty pathspec lists
   the whole repo). If a KB dir is the project root, take only the generated files,
   never the whole root. With no workstation, also include `.avengers/kb.json` if
   tracked. Legacy marker: if `git ls-files --deleted -- .avengers/kb.json` is non-empty
   (moved by this stamp or an earlier /bmad stamp), its deletion is a candidate even if
   no KB doc changed; with no in-repo KB dirs it is the only possible candidate. If there
   are no candidates, report "no in-repo KB files to commit". Otherwise dispatch Thor to
   commit all candidates in one commit, `docs: refresh project KB`; for the legacy
   deletion, Thor runs `git rm --cached --quiet -- .avengers/kb.json` as part of that
   dispatch. Never amend it after stamping. The KB stays fresh because `status`
   computes signals over stamped..HEAD and excludes those paths. The commit is generated
   documentation, not a code change, so Captain review is not required. If Thor's commit
   fails, report "KB stamped but docs not committed". Without a workstation, list KB
   files outside the repo in the final report; they are not committed.
3. md commit: only if `workstation` is set and step 1 ended stamped (exit 0, exit 2, or
   confirmed on re-check), after step 2.
   Follow relay-config §3.11 (md commits) with `<phase>` = `kb-sync`: IronMan runs
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py md-status`
   (exit 2 -> skip silently; exit 1 -> note it and continue). On exit 0, warn first if
   `dedicated` is false, then ask "Commit <count> md changes in <toplevel>?". On yes,
   Thor runs `git -C <toplevel> add -- <rel>`, then
   `git -C <toplevel> commit -m "docs(<repo_name>): kb-sync artifacts" -- <rel>`. Never
   push; a failure is reported and does not block.

On no: record "KB refresh declined" in the final report.

Record `<start-sha>` in the final report for traceability.

`${CLAUDE_PLUGIN_ROOT}` is the plugin directory this scheme was loaded from; substitute
the absolute path if the variable is not set in the shell.

## Completion Criteria

- [ ] Root cause identified
- [ ] Fix implements targeting root cause
- [ ] Regression test added
- [ ] Full test suite passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS
- [ ] Code committed
- [ ] KB refreshed if impact flagged (outcome recorded: refreshed / declined / deferred / skipped; md commit offered if workstation set)
