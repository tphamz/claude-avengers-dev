# Avengers Dev – Testing Playbook

## How to Test a Skill Change

1. Make your changes to scripts and/or SKILL.md files
2. Open a test session in a clean test directory. `tools/make-debug-fixture.py`
   builds one and prints the exact commands (see
   [Debug-session checklist](#debug-session-checklist)):
   ```bash
   claude --debug --plugin-dir /path/to/avengers-dev
   ```
3. Run the skill being tested (e.g., `/avengers-init`)
4. Return to the dev session and run `/debug-session`
5. The skill produces a verdict: **CLEAN**, **PARTIAL**, or **FAILED**
6. If not CLEAN: fix the issues, repeat from step 2
7. Only commit when the verdict is CLEAN

## What CLEAN means

- Zero `Bash tool error` entries from our scripts
- Zero permission prompts
- Zero Write/Edit tool failures
- All expected files created/modified
- The agent did not improvise or deviate from the SKILL.md instructions

## Environment noise to ignore in debug logs

These appear in every session and are NOT skill failures:

- `API error (attempt 1/11): 404` – streaming endpoint fallback
- `Fast mode unavailable` – polling noise
- `Failed to fetch org fast mode status` – SSL startup
- `rg error ... plugins/cache` – missing cache directory

## Script Unit Tests

Bundled scripts with non-trivial logic ship with stdlib `unittest` suites under
`tests/`. Run them from the plugin root:

```bash
python3 -m unittest discover -s tests -v
```

- `tests/test_bmad_kb.py` covers `skills/bmad/scripts/bmad-kb.py` (config parsing,
  preflight, KB status, impact signals, stamp). Each case builds its own temporary
  git repo, so the suite needs only `git` and Python 3 on `PATH`.
- `tests/test_doc_consistency.py` keeps facts that are written in several places in
  agreement: the /bmad and /sdd phase tables, the numbered workflow lists in
  `CLAUDE.md` and the persona, the track chains, relay-config `§` citations, the
  equipment registries, the skill list, `ensure-bmad.py`'s file list, and the plugin
  version. A failure names the file, the line, and what was expected. If you change
  a phase, a piece of equipment, a skill or a `§` section, update every copy the
  test names.
- `tests/test_script_smoke.py` runs `--help` on every `skills/*/scripts/*.py` and
  `tools/*.py`, which catches import-time errors on older Pythons.

Version floors: Python >= 3.9 and git >= 2.32 (the tests isolate git with
`GIT_CONFIG_GLOBAL`). The OpenSpec integration test in `tests/test_sdd_openspec.py`
is skipped unless `OPENSPEC_BIN` points at an `openspec` binary.

Unit tests complement, not replace, the debug-session check above: a skill change
still needs a CLEAN `/debug-session` verdict before committing.

## CI

`.github/workflows/tests.yml` runs on every pull request and on pushes to `main`:

| Job | Where | What |
| --- | ----- | ---- |
| `unit` | Python 3.9 on ubuntu-24.04, 3.12 on ubuntu-latest, 3.12 on macos-latest | git >= 2.32 check, `compileall` on `skills tests tools`, `bash -n` on the shell scripts, then `python -m unittest discover -s tests -v` |
| `openspec-integration` | ubuntu-latest, Python 3.12, Node 22 | installs OpenSpec 1.13.2 into the runner's temp dir and runs `tests.test_sdd_openspec` with `OPENSPEC_REQUIRED=1` |

With `OPENSPEC_REQUIRED=1` the integration test fails instead of skipping when
`OPENSPEC_BIN` is unset, missing, or not executable, so a broken install cannot pass
silently. To reproduce the OpenSpec job locally:

```bash
npm i --no-save --prefix /tmp/os @fission-ai/openspec@1.13.2
OPENSPEC_BIN=/tmp/os/node_modules/.bin/openspec OPENSPEC_REQUIRED=1 \
  OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 python3 -m unittest tests.test_sdd_openspec -v
```

CI does not replace the debug session: a skill change still needs a CLEAN
`/debug-session` verdict.

## Debug-session checklist

Build a throwaway fixture first. It never touches your real HOME and prints the
commands to run next:

```bash
python3 tools/make-debug-fixture.py --dest /tmp/avengers-fixture
```

It creates `md-root/` (a dedicated md git repo), `remote.git` (a bare repo, added to
`app` as the remote `local`), `app/` (a small Python module with a test; `origin` is
the fake `git@github.com:fixture/app.git`, so the workstation is `app-mds`),
`app-wt/` (a second worktree of `app`) and `home/`. `home/` is only for running
`workstation.py` or `openspec` by hand; `claude` runs with your real HOME so the
login is kept, which means skills in the session write the registry to your real
`~/.avengers/workstations.json`. Remove that entry afterwards if you want a clean
slate. `--force` rebuilds a fixture; it deletes only a directory that holds the
tool's own marker file. `npx bmad-method install` and the OpenSpec install are
printed as hints, never run.

Run each scenario in `claude --debug --plugin-dir <repo>` from `app/` (or `app-wt/`
where noted), then run `/debug-session` in the dev session.

**Workstation**

| # | Scenario | Expected result |
|---|----------|-----------------|
| 1 | `/avengers-workstation`, give `<fixture>/md-root` as the md root | `<fixture>/md-root/app-mds/` exists; `.avengers/settings.json` records it; the registry maps `github.com/fixture/app` to it; the path is in `permissions.additionalDirectories` |
| 2 | Ask Claude to search for a string that lives only in a workstation file: once from the repo root, once with the explicit workstation path | The root search misses it (the symlink is not followed); the explicit-path search finds it, as `.claude/rules/avengers-kb.md` instructs |
| 3 | From `app-wt/`, `/avengers-workstation status` | `state: ok` with the same path, no question asked (same `remote_key` as `app/`) |
| 4 | Delete `md-root/app-mds/`, run `status`; answer the question with "in-repo" | First `state: broken`, and the skill asks for the md root again; after "in-repo", `state: in_repo` and no managed symlinks remain |
| 5 | Re-wire as in 1, then `/avengers-uninstall` | The symlinks, `.avengers/` and the grant are removed; `md-root/app-mds/` and its contents are still there |

**/sdd** (needs OpenSpec >= 1.13 on `PATH`)

| # | Scenario | Expected result |
|---|----------|-----------------|
| 6 | `/sdd add-farewell quick` | 0 → P (lite) → B → V → A with no gate; the change is archived under `openspec/changes/archive/` and the spec lands in `openspec/specs/` |
| 7 | `/sdd add-shout standard` | E/P produce proposal, specs, design, tests, tasks; Captain hardens, Hulk returns readiness; the gate stops for [1]/[2]; after [1], Thor writes the failing tests from `tests.md` before working `tasks.md` |
| 8 | `/sdd add-report full` (with BMAD installed) | The state file is written with `status: handed_off` and `/bmad add-report full` takes over |
| 9 | With `openspec/` committed in `app/`, run `/sdd` and choose to keep it in the repo | `mdLinksInRepo: ["openspec"]`; `openspec/` stays a real directory; after archive Thor commits `docs(openspec): archive <change>` in the code repo |

**/bmad** (needs `npx bmad-method install` in `app/`)

| # | Scenario | Expected result |
|---|----------|-----------------|
| 10 | `/bmad tidy quick` | Phase 0 → `bmad-quick-dev` → Captain reviews the diff → Phase 9; no gate |
| 11 | `/bmad greet-v2 standard`, run through Phase 4.5 | Phases 0 → 1a (KB missing) → 1b → 2 → 3 → 4 run in the main loop, each with a boundary confirmation; Phase 4.5 dispatches Captain with the `adversarial` lens and Captain assigns the severity tags; the state file shows `current_phase: 4.5` |
| 12 | `/bmad greet-v3 full` without the TEA module (`_bmad/tea/` absent) | Preflight reports `TEA_MISSING`; the skill asks to downgrade to `standard` or stop, with no silent fallback |

**Schemes**

| # | Scenario | Expected result |
|---|----------|-----------------|
| 13 | With a stamped KB and a workstation, run a small feature through `avengers-assemble` | Phase 6 KB Sync runs `bmad-kb.py impact`, asks before a refresh, and offers the md commit with `<phase>` = `kb-sync` |

**Finally:** `/debug-session` on each log returns **CLEAN**.
