---
name: disable-ironman
description: Deactivate the IronMan persona for this project by removing the avengers-dev rules file.
allowed-tools: Bash, Read
---

# Disable IronMan Persona

## Steps

### 1. Check State

```bash
test -f .claude/rules/avengers-dev.md && echo "EXISTS" || echo "NOT_FOUND"
```

If NOT_FOUND: Report "IronMan not active in this project" and exit.

### 2. Remove Rules File

```bash
rm .claude/rules/avengers-dev.md
```

### 3. Confirm

Report: "IronMan disabled. Changes take effect on next Claude Code session start."
