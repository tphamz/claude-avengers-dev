# spec-target: deterministic spec Target; gated md-repo commit for workstation specs

## Objective
Give Hulk and Thor one scripted answer to "where does the spec go and may it be
committed in the md repo". Commit workstation specs in the md repo only with
informed, still-valid consent.

## Scope

**Files to Create/Modify/Delete**
- `skills/avengers-workstation/scripts/workstation.py` — new `spec-target --slug`; shared toplevel/rel/dedicated helper used by spec-target and md-status; resolve() untouched
- `tests/test_workstation.py` — spec-target tests
- `scripts/session-start.sh`, `scripts/compact-resume.sh` — print `Avengers plugin root: <realpath>`
- `agents/hulk.md` — drafting rule (canonical); sign-off fields
- `agents/thor.md` — re-resolve, save, commit gate, generic Blocked variant; remove TODO(workstation)
- `personas/ironman.md` (~148-156, 204-206, 215-217) — absolute script path from the plugin-root line; plan shows Target / Workstation state / md commit; consent rule
- `CLAUDE.md` (~93), `README.md` (~94), `skills/avengers-workstation/SKILL.md` — pointers; layout line; spec-target documented

## Acceptance Criteria
- [ ] `spec-target` prints {state, spec_dir, target, commit:{git, toplevel, pathspec, dedicated, reason}}; exit 0 success, 1 error; never 2; read-only
- [ ] Workstation `spec_dir` = realpath(path)/avengers/specs/stories only when resolve's `source` is `project` or `registry` and that path is an existing directory, whatever the link state (a dangling `_bmad-output` or `openspec` link never moves specs); otherwise <realpath(repo)>/specs/stories (`guess`, `in_repo`, `missing`, folder gone)
- [ ] Slug must match `^[a-z0-9][a-z0-9-]{0,79}$`; otherwise exit 1 with a stderr message
- [ ] spec-target `pathspec` matches md-status `dirty` entries exactly (shared helper; rel "." gives no `./`)
- [ ] The session-start and compact-resume hooks print the plugin root; Tony passes the absolute workstation.py path in every Hulk and Thor dispatch and never guesses it
- [ ] Hulk's sign-off shows Target, Workstation state and md commit; a spec-target failure is shown, and the Target falls back in-repo
- [ ] Thor: an in-repo Target is always saved in-repo; a workstation Target must equal the fresh `target`, else Blocked; a denied Write or mkdir gives the generic Blocked report
- [ ] Thor commits in the md repo only when git=true, dedicated=true, fresh toplevel == approved toplevel, and the pathspec is in md-status `dirty`; otherwise the spec stays uncommitted, with the reason (plus the §3.11 warning when dedicated=false)
- [ ] Never push; md-commit failures (hook, signing, merge in progress) are reported and never block
- [ ] Scoped greps are clean; `python3 -m unittest discover -s tests` passes; `bash -n scripts/*.sh` passes
- [ ] Debug session CLEAN: dedicated repo (one spec-only md commit), non-dedicated (no commit + warning), re-pointed (Blocked), plugin-root line present after startup and compaction, absolute path works in a subagent

## Tasks
- [ ] Commit 1 `feat(workstation): spec-target subcommand`: helper refactor, spec-target, tests (every state; guess -> in-repo; dangling link with folder present -> workstation; symlinked root; rel "."; $HOME toplevel; toplevel containing the project; no git; slug rejects `/`, `..`, empty, leading dot; pathspec is in md-status dirty; --help)
- [ ] Commit 2 `docs(agents): resolve spec target via spec-target; gated md-repo commit`: hooks' plugin-root line, hulk.md, thor.md, persona, CLAUDE.md, README.md, workstation SKILL.md; save this spec to its Target
- [ ] Run the tests before each commit; do not push

## Engineering Notes (Hulk)
- The plugin root must come from the hook line: CLAUDE_PLUGIN_ROOT is empty in Bash, and `pluginDirectory` (/Users/tanpham/avengers-dev) differs from the running plugin (~/.claude/plugins/avengers-dev).
- `state: broken` next to a workstation Target is intended (only a link dangles).
- Consent is per toplevel: if it changes after approval, Thor does not commit.
- Merge overlap with `claude/sdd-openspec`: ironman.md, CLAUDE.md, workstation SKILL.md, README.md, workstation.py argparse and md-status internals, the session scripts.

## Status
- [x] Spec approved by user
