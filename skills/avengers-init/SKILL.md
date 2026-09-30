---
name: avengers-init
description: >
  Full environment setup for Avengers Dev. Run once per project to activate
  the IronMan persona, configure SSL if needed, and set up the .avengers/ directory.
allowed-tools: Bash, Read, Write
argument-hint: "[--dry-run] [--ssl] [--git-workflow]"
---

# Avengers Init - Full Environment Setup

## Overview

Run this once per project to activate Avengers Dev. It:
1. Creates `.avengers/settings.json` for the project
2. Detects and configures SSL certificate bundle (if in TLS proxy environment)
3. Generates `.claude/rules/avengers-dev.md` to activate IronMan
4. Optionally sets up git workflow rules

## Steps

### 1. Run avengers-init.py

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-init/scripts/avengers-init.py \
  --plugin-dir ${CLAUDE_PLUGIN_ROOT} \
  --project-dir . \
  [--dry-run]
```

Exit 0: success. Exit 1: error. Exit 2: already initialized (no-op).

### 2. Run ensure-bmad.py

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-init/scripts/ensure-bmad.py \
  --plugin-dir ${CLAUDE_PLUGIN_ROOT}
```

Verifies the 13 BMAD reference stubs under `references/bmad/` (relay config,
Phase 0–9 stubs including 4.5, and the quick-track stub) exist and are non-empty.
Exit 0: success (missing files are reported as a warning on stderr). Exit 1:
`references/bmad/` not found.

### 3. Configure SSL (if --ssl flag or TLS proxy detected)

Run `/avengers-ssl` to generate CA bundle.

Report the env var exports to add to shell profile.

### 4. Configure Git Workflow (if --git-workflow flag)

Run `/git-workflow enable`.

### 5. Report

```
Avengers Dev Initialized
========================
Project: {cwd}
Plugin: {plugin-dir}

Created:
  ✓ .avengers/settings.json
  ✓ .claude/rules/avengers-dev.md
  ✓ .avengers/relay-sequences/ (directory)

IronMan is now active for this project.
Run /enable-ironman to re-enable after /disable-ironman.
```
