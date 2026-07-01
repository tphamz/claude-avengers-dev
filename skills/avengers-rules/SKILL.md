---
name: avengers-rules
description: >
  Manage project rules. Commands: list, install, remove.
  Rules are markdown files that Claude Code auto-loads from .claude/rules/.
allowed-tools: Bash, Read, Write, Glob
argument-hint: "list | install <rule-name> | remove <rule-name>"
---

# Avengers Rules - Project Rules Manager

## Commands

### `list`

Run the catalog script to show available and installed rules:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-rules/scripts/manage-catalog.py list \
  --plugin-dir ${CLAUDE_PLUGIN_ROOT} \
  --project-dir .
```

Output shows:
- Available rules (in plugin's rules/ directory)
- Installed rules (in project's .claude/rules/)
- Status for each: installed / available / custom (not from plugin)

### `install <rule-name>`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-rules/scripts/manage-catalog.py install \
  --plugin-dir ${CLAUDE_PLUGIN_ROOT} \
  --project-dir . \
  <rule-name>
```

Copies rule from plugin to `.claude/rules/<rule-name>.md`.

Exit 0: installed. Exit 1: error. Exit 2: already installed (no-op).

### `remove <rule-name>`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-rules/scripts/manage-catalog.py remove \
  --plugin-dir ${CLAUDE_PLUGIN_ROOT} \
  --project-dir . \
  <rule-name>
```

Removes `.claude/rules/<rule-name>.md`.

Exit 0: removed. Exit 1: error. Exit 2: not installed (no-op).

## Available Rules

Rules live in the plugin's `.claude/rules/` directory:
- `ironman-delegation` - IronMan Agent() delegation enforcement
- `development-standards` - Configuration architecture and script standards
- `pr-acceptance` - PR acceptance gates checklist
- `serious-mode` - Suspend themed voice: plain, information-first tone and reporting (process gates unchanged)
