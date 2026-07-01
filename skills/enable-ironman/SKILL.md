---
name: enable-ironman
description: >
  Activate the IronMan persona for this project. Creates .claude/rules/avengers-dev.md
  with @include references to the ironman persona. IronMan is activated on next session start.
allowed-tools: Bash, Read, Write
---

# Enable IronMan Persona

## Steps

### 1. Check Current State

```bash
test -f .claude/rules/avengers-dev.md && echo "EXISTS" || echo "NOT_FOUND"
```

If EXISTS: Check if IronMan is already included. If so, report "IronMan already enabled" and exit (no-op).

### 2. Detect Plugin Directory

```bash
python3 -c "import json,pathlib; s=json.load(open(pathlib.Path.home()/'.avengers'/'settings.json')); print(s['pluginDirectory'])" 2>/dev/null || echo "NOT_CONFIGURED"
```

If NOT_CONFIGURED: instruct user to run `/avengers-init` first.

### 3. Write Rules File

Create `.claude/rules/avengers-dev.md`:

```markdown
# Avengers Dev - Active Rules

@include {PLUGIN_DIR}/personas/ironman.md
@include {PLUGIN_DIR}/.claude/rules/ironman-delegation.md
```

Where `{PLUGIN_DIR}` is the detected plugin directory (absolute path).

### 4. Add to .gitignore

The rules file contains absolute paths (machine-specific). Add to `.gitignore`:

```
.claude/rules/avengers-dev.md
```

### 5. Confirm

Report: "IronMan enabled. Active on next Claude Code session start in this project."
