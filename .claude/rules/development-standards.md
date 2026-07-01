# Avengers Dev – Development Standards

## Configuration Architecture

### The `.avengers/` Directory

The framework uses `.avengers/` as its configuration namespace.

- **`~/.avengers/`** - Home-level global defaults (CA bundle, global settings)
- **`<project>/.avengers/`** - Project-level settings

Both contain `settings.json` with at minimum `version` and `pluginDirectory`.

### The `.claude/rules/avengers-dev.md` Pattern

The plugin injects persona and workflow instructions via a generated rules file
at `.claude/rules/avengers-dev.md`. This file:

- Is **auto-loaded** by Claude Code
- Contains `@include` directives with absolute paths to plugin files
- Is **generated** by `/avengers-init`
- Is **gitignored** (absolute paths are machine-specific)
- **Never** lives in `~/.claude/` – only in the project directory

### The Portability Principle

**Avengers Dev must NEVER modify files in `~/.claude/`.**
All framework state lives in `.avengers/` directories, project-level `.claude/rules/`,
or the plugin's own `settings.json`.

**Specifically:**
- Spinner verbs -> `avengers-dev/settings.json` (plugin-scoped, auto-loaded with plugin)
- SSL env vars -> project `~/.claude/settings.local.json` (written by `avengers-init`, project-scoped)
- Git instructions -> project `~/.claude/settings.local.json` (written by `avengers-init`)
- Persona includes -> project `.claude/rules/avengers-dev.md` (written by `avengers-init`)
- CA bundle -> `~/.avengers/ca-bundle.pem` (home-level, avengers namespace only)

**Never write to:**
- `~/.claude/settings.json`
- `~/.claude/settings.local.json`
- `~/.claude/CLAUDE.md`
- Any other file under `~/.claude/`

## Skill Script Standards

### Scripts, Not Inline Code

Skills MUST use bundled Python scripts for all non-trivial operations.
The `SKILL.md` is a **declarative instruction document** – it tells Claude which
scripts to run and how to interpret their output. No inline bash or python code blocks.

### The `--dry-run` Pattern for Protected Files

Scripts that modify `.claude/settings.local.json` MUST support `--dry-run`:

1. Script computes the merged/updated JSON
2. With `--dry-run`: prints JSON to stdout
3. The `SKILL.md` instructs Claude to write the stdout content using the Write tool

### Script Requirements

Every script MUST:
1. Use `argparse` for CLI interface with `--help`
2. Use only Python stdlib
3. Use `pathlib.Path` for all file operations
4. Exit codes: 0 = success, 1 = error, 2 = no-op
5. Print errors to stderr
6. Handle malformed JSON gracefully (backup as `.json.bak`)
7. Work on both macOS and Linux

## Skill Testing Workflow

Every skill change MUST be validated with a debug session before committing.

1. Make changes
2. Open a test session: `claude --debug --plugin-dir /path/to/avengers-dev`
3. Run the skill being tested
4. Return and run `/debug-session`
5. Verdict must be CLEAN before committing
