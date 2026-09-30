---
name: avengers-uninstall
description: >
  Remove Avengers Dev configuration from the current project.
  Removes .avengers/ directory, .claude/rules/avengers-dev.md,
  and reverts settings.local.json changes.
allowed-tools: Bash, Read, Write
argument-hint: "[--dry-run]"
---

# Avengers Uninstall - Remove Project Configuration

## Warning

This removes Avengers Dev configuration from this project only.
It does NOT remove the plugin itself or affect other projects.

## Steps

### 1. Inventory What Will Be Removed

Check what exists:
- `.avengers/` directory
- `.claude/rules/avengers-dev.md`
- `.claude/rules/avengers-kb.md`
- md workstation wiring — run
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py resolve`
  (exit 0: JSON; `symlink` and `path` show what is wired)

Report what will be removed. If `--dry-run` is provided, stop here.

### 2. Confirm with User

"This will remove Avengers Dev configuration from this project. Continue? [yes/no]"

If not yes, abort.

### 3. Revert md Workstation Wiring

Skip if `resolve` reported no `path`. Do this **before** removing `.avengers/`,
because the scripts read the project setting from it.

1. Record the grant path:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py grant-path`
   (exit 0: prints the realpath; exit 1: nothing resolved — skip item 3).
2. Remove the symlink, the project setting, and the `.git/info/exclude` lines:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py unlink`
   (exit 0: removed, JSON `kept` is the workstation path; exit 2: nothing wired).
3. Revoke the directory grant:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-init/scripts/manage-settings.py list-remove --key permissions.additionalDirectories --value <grant path> --dry-run`
   Exit 0: write the printed JSON to `.claude/settings.local.json` with the Write
   tool. Exit 2: not granted, nothing to write.

The workstation contents and the `~/.avengers/workstations.json` entry are kept.

### 4. Remove Files

```bash
rm -rf .avengers/
rm -f .claude/rules/avengers-dev.md
rm -f .claude/rules/avengers-kb.md
```

### 5. Confirm

Report: "Avengers Dev removed from this project. The plugin is still installed globally."
If a workstation was unlinked, add: "Your markdown is kept at {kept}."
