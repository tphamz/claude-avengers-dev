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
5. Optionally sets up an md workstation (external home for markdown artifacts)

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

### 5. md Workstation (optional)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py resolve
```

Exit 0: JSON with `state`. Exit 1: report the error and skip this step.

- `ok` — already set up; if `symlink` is not `ok`, run `workstation.py set --path <path>`.
- `in_repo` — the user chose in-repo before; skip.
- `missing` — ask, as a plain chat question: "Where should this repo's markdown live?
  Give an md root folder (the workstation will be `<root>/<repo_name>`), or answer
  in-repo." For in-repo, run `workstation.py set --in-repo` and skip the rest.
- `guess` — ask to confirm `path`.
- `broken` — say the recorded folder is gone, then ask as for `missing`.

Then follow `/avengers-dev:avengers-workstation` Steps 2–5: `set` (or `migrate`
when the output folder already holds content), grant access through
`manage-settings.py list-add --dry-run` plus the Write tool, then `check-config`
with a per-key opt-in `repoint-config`. Exit codes are documented there.

### 6. Report

```
Avengers Dev Initialized
========================
Project: {cwd}
Plugin: {plugin-dir}

Created:
  ✓ .avengers/settings.json
  ✓ .claude/rules/avengers-dev.md
  ✓ .avengers/relay-sequences/ (directory)
  ✓ md workstation: {path | in-repo | skipped}

IronMan is now active for this project.
Run /enable-ironman to re-enable after /disable-ironman.
```
