---
name: avengers-workstation
description: >
  Set up or inspect the md workstation — a folder outside the code repo that holds
  all Avengers + BMAD + OpenSpec markdown for it, at <md-root>/<repo-name>-mds/.
  BMAD's output_folder and (for /sdd) openspec/ become symlinks into it.
  Commands: status, set, root, migrate, unlink.
allowed-tools: Bash, Read, Write
argument-hint: "[status|set <path>|root <md-root>|migrate|unlink]"
---

# Avengers Workstation - External Home for Markdown

## Overview

The md workstation keeps a repo's markdown artifacts out of the code repo — for
example in one central md repo that holds the docs for many code repos. Layout:

```
<md-root>/<repo-name>-mds/      <- BMAD output_folder (_bmad-output) symlinks here
  planning-artifacts/ implementation-artifacts/ project-knowledge/ project-context.md
  avengers/specs/stories/<slug>.md    (Hulk specs)
  avengers/kb.json                    (KB freshness marker)
  openspec/                           <- openspec/ symlinks here (/sdd only)
```

- **Managed links.** Each link is a directory symlink in the project, recorded in
  `.avengers/settings.json` → `mdLinks`:

  | Link | In the project | Target | Managed when |
  | ---- | -------------- | ------ | ------------ |
  | `bmad` | BMAD `output_folder` (`_bmad-output`) | the workstation | `_bmad/` exists, `mdLinks` lists it, or no `mdLinks` is recorded yet (older installs) |
  | `openspec` | `openspec/` | `<workstation>/openspec/` | `set --link openspec` (run by `/sdd`) |

  Without BMAD, `/sdd` wires only the `openspec` link — there is no `_bmad-output`.
- The symlinks are ignored through `.git/info/exclude` (per clone), never `.gitignore`.
- `.claude/rules/avengers-kb.md` (also excluded) tells agents where the markdown
  lives. Default `rg`, `grep -r` and `find` do not follow the symlink, so agents
  search by explicit path or with `grep -R` / `find -L`. Once
  `project-context.md` exists, the file also imports it.
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

Exit 0: JSON `{state, path, source, root, remote_key, repo_name, suggested_path,
output_folder, symlink, symlinks}`. `symlinks` maps each managed link to
`ok|missing|dangling|mismatch|real_dir`; `symlink` is the `bmad` link, kept for
older callers. `resolve --link openspec` also reports the `openspec` link before it
is managed (`/sdd` uses this).
Exit 1: error — report it and stop.

With `status` (or no argument), report the JSON in plain words, then act on `state`:

| `state` | Meaning | Action |
| ------- | ------- | ------ |
| `ok` | workstation found | if any `symlinks` value is not `ok`, run Step 2 with `path` (repair, no question) |
| `guess` | `<root>/<repo-name>-mds/` exists but is not registered | ask "Use `<path>` as the md workstation for this repo?"; on yes, Step 2 |
| `missing` | nothing recorded | ask for the md root folder, or "in-repo" to keep markdown in the repo |
| `broken` | the recorded folder is gone, or a managed symlink dangles | say so, then ask as for `missing` |
| `in_repo` | the user chose to keep markdown in the repo | report it; nothing to do |

For `missing`/`broken`: the answer is the md **root**; the workstation path is
`<root>/<repo_name>-mds` (`set --root <root>` uses it by default). If the user
answers "in-repo", run `workstation.py set --in-repo` and stop. It removes any
existing managed symlink (`_bmad-output`, `openspec`), its exclude lines,
`mdLinks` and `avengers-kb.md` (a real directory is never touched). Exit 0
recorded; exit 2 already recorded.

### 2. Set (`set <path>`)

If a link folder (the output folder, or `openspec/` with `--link openspec`) is a
non-empty real directory, go to Step 3 instead.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py set --path <path> [--root <md-root>] [--link openspec] [--dry-run]
```

Each link's target is created before the link. Pass `--link openspec` when the
caller (e.g. `/sdd`) needs `openspec/` managed; it is recorded in `mdLinks`, so a
later plain `set` keeps it.

Exit 0: wired — JSON lists the `links` and the actions taken. Exit 2: already set
(no-op). Exit 1: refused or failed — relay stderr. Common refusals:

- a link folder is a non-empty directory, or tracked in git → Step 3 (`migrate`,
  with `--link openspec` for `openspec/`; teams often commit `openspec/`)
- the folder is already registered to another repo → suggest the `<org>-<repo>-mds`
  name from stderr and ask the user to confirm it

A `bmad-story-automator` warning on stderr is informational; pass it on.

Then continue with Steps 4 and 5.

### 3. Migrate (`migrate`)

Moves existing in-repo output into the workstation, then wires it as in Step 2.
Always preview first:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py migrate --path <path> [--link openspec] --dry-run
```

`--link openspec` moves `openspec/` into `<path>/openspec/`; the default is the
BMAD output folder.

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

Exit 0: every path key is inside the output folder. Exit 1: `_bmad/` missing, or
`output_folder` is outside the project — relay stderr and skip this step. Exit 2: JSON `outside` lists keys that resolve elsewhere (typically
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
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py set --root <md-root>
```

The workstation defaults to `<md-root>/<repo_name>-mds`. Exit codes as in Step 2.

### 7. Unlink (`unlink`)

First run `workstation.py grant-path` and keep its output (exit 1: nothing resolved;
skip the revoke below). Then:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py unlink [--dry-run]
```

Removes every managed symlink, the project settings (`mdWorkstation`, `mdLinks`),
`.claude/rules/avengers-kb.md`, and the `.git/info/exclude` lines. The exclude file is shared by all worktrees of a clone,
so lines another worktree still uses are kept — JSON `exclude_kept` names them;
report it. Never touches the workstation contents or `~/.avengers/workstations.json`.
Exit 0: removed — JSON `kept` is the preserved workstation path; report it. Exit 2:
nothing to remove.

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
Symlinks:   {output_folder} -> {path}; openspec -> {path}/openspec (if managed)
Granted:    {grant-path}
Outside keys: {re-pointed / declined / none}
```
