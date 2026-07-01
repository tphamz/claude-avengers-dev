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

Report what will be removed. If `--dry-run` is provided, stop here.

### 2. Confirm with User

"This will remove Avengers Dev configuration from this project. Continue? [yes/no]"

If not yes, abort.

### 3. Remove Files

```bash
rm -rf .avengers/
rm -f .claude/rules/avengers-dev.md
```

### 4. Confirm

Report: "Avengers Dev removed from this project. The plugin is still installed globally."
