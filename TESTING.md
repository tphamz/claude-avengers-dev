# Avengers Dev – Testing Playbook

## How to Test a Skill Change

1. Make your changes to scripts and/or SKILL.md files
2. Open a test session in a clean test directory:
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

Unit tests complement, not replace, the debug-session check above: a skill change
still needs a CLEAN `/debug-session` verdict before committing.
