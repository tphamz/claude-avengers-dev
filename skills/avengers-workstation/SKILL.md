---
name: avengers-workstation
description: >
  Set up or inspect the md workstation — a folder outside the code repo that holds
  all Avengers + BMAD markdown for it, at <md-root>/<repo-name>/. BMAD's
  output_folder becomes a symlink to it. Commands: status, set, root, migrate, unlink.
allowed-tools: Bash, Read, Write
argument-hint: "[status|set <path>|root <md-root>|migrate|unlink]"
---

# Avengers Workstation - External Home for Markdown

## Overview

The md workstation keeps a repo's markdown artifacts out of the code repo — for
example in one central md repo that holds the docs for many code repos. Layout:

```
<md-root>/<repo-name>/          <- BMAD output_folder (_bmad-output) symlinks here
  planning-artifacts/ implementation-artifacts/ project-knowledge/ project-context.md
  avengers/specs/stories/<slug>.md    (Hulk specs)
  avengers/kb.json                    (KB freshness marker)
```

- The symlink is ignored through `.git/info/exclude` (per clone), never `.gitignore`.
- BMAD config stays relative, so it is still portable for the team.
- `~/.avengers/workstations.json` remembers the md root and each repo's folder, so
  other clones and worktrees find it without asking.
- **Limitation:** `bmad-story-automator` rejects artifact paths that resolve outside
  the repo root, so it does not work with a workstation. The Avengers relay does not
  use it.
- **Forks:** the registry is keyed by the remote URL (`origin`, else `upstream`, else
  the first remote), so a fork gets its own entry.

The script is `${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py`
(referred to below as **workstation.py**). Every subcommand accepts `--project-dir`
(default: current directory) and prints `--help`. It refuses to run on Windows (exit 1).

> **Prompting:** every question below is a plain chat question. Ask it directly and
> wait for the reply. Do not use a structured question tool.

## Steps

### 1. Resolve

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py resolve
```

Exit 0: JSON `{state, path, source, root, remote_key, repo_name, output_folder, symlink}`.
Exit 1: error — report it and stop.

With `status` (or no argument), report the JSON in plain words, then act on `state`:

| `state` | Meaning | Action |
| ------- | ------- | ------ |
| `ok` | workstation found | if `symlink` is not `ok`, run Step 2 with `path` (repair, no question) |
| `guess` | `<root>/<repo-name>/` exists but is not registered | ask "Use `<path>` as the md workstation for this repo?"; on yes, Step 2 |
| `missing` | nothing recorded | ask for the md root folder, or "in-repo" to keep markdown in the repo |
| `broken` | the recorded folder is gone, or the symlink dangles | say so, then ask as for `missing` |
| `in_repo` | the user chose to keep markdown in the repo | report it; nothing to do |

For `missing`/`broken`: the answer is the md **root**; the workstation path is
`<root>/<repo_name>`. If the user answers "in-repo", run
`workstation.py set --in-repo` (exit 0 recorded; exit 2 already recorded) and stop.

### 2. Set (`set <path>`)

If the output folder is a non-empty real directory, go to Step 3 instead.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py set --path <path> [--root <md-root>] [--dry-run]
```

Exit 0: wired — JSON lists the actions taken. Exit 2: already set (no-op).
Exit 1: refused or failed — relay stderr. Common refusals:

- output folder is a non-empty directory, or tracked in git → Step 3 (`migrate`)
- the folder is already registered to another repo → suggest the `<org>-<repo>`
  name from stderr and ask the user to confirm it

A `bmad-story-automator` warning on stderr is informational; pass it on.

Then continue with Steps 4 and 5.

### 3. Migrate (`migrate`)

Moves existing in-repo output into the workstation, then wires it as in Step 2.
Always preview first:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py migrate --path <path> --dry-run
```

Show the moves and any `.conflict` names (a name clash with different content keeps
both copies), then ask to proceed. Run again without `--dry-run`.

Exit 0: migrated. Exit 2: nothing to migrate. Exit 1: refused or failed.

**Tracked output folder.** If exit 1 says the folder is tracked, stderr carries a
warning. Repeat it to the user plainly: once the `git rm -r --cached` is committed
and pushed, **every teammate who pulls loses their working copy** of that folder.
Only on an explicit yes, re-run with `--untrack`. Recommend leaving the untrack
uncommitted until the team agrees.

Then continue with Steps 4 and 5.

### 4. Grant Claude Code access

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py grant-path
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-init/scripts/manage-settings.py list-add --key permissions.additionalDirectories --value <grant-path output> --dry-run
```

`grant-path` exit 0 prints the realpath. `list-add` exit 0 prints the merged JSON —
write it to `.claude/settings.local.json` with the Write tool. Exit 2: already
granted, nothing to write. Exit 1: report the error.

### 5. BMAD config keys outside the output folder

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py check-config
```

Exit 0: every path key is inside the output folder. Exit 1: `_bmad/` missing — skip
this step. Exit 2: JSON `outside` lists keys that resolve elsewhere (typically
`project_knowledge` → `docs/`). Those artifacts stay in the repo unless re-pointed.

For each entry with `declined: false`, ask one key at a time, with the warning:
"Re-pointing `<key>` edits `<file>`, which is usually committed — it changes the
config for the whole team. Re-point to `<suggested>`?"

- Yes: `workstation.py repoint-config --key <key> --dry-run`, show the change, then
  run it without `--dry-run`. Exit 0 changed (a `.bak` is kept); exit 2 already
  inside; exit 1 error. Existing files at the old location are not moved.
- No: `workstation.py repoint-config --key <key> --decline` (exit 0 recorded; exit 2
  already recorded), so it is not asked again.

### 6. Root (`root <md-root>`)

Records the md root for future repos:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py set --path <md-root>/<repo_name> --root <md-root>
```

Exit codes as in Step 2.

### 7. Unlink (`unlink`)

First run `workstation.py grant-path` and keep its output (exit 1: nothing resolved;
skip the revoke below). Then:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py unlink [--dry-run]
```

Removes the symlink, the project setting, and the `.git/info/exclude` lines. Never
touches the workstation contents or `~/.avengers/workstations.json`. Exit 0:
removed — JSON `kept` is the preserved workstation path; report it. Exit 2: nothing
to remove.

Then revoke the access grant:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-init/scripts/manage-settings.py list-remove --key permissions.additionalDirectories --value <grant-path output> --dry-run
```

Exit 0: write the printed JSON with the Write tool. Exit 2: nothing to remove.

### 8. Report

```
md workstation
==============
Repo:       {repo_name} ({remote_key})
Workstation: {path}
Symlink:    {output_folder} -> {path}
Granted:    {grant-path}
Outside keys: {re-pointed / declined / none}
```
