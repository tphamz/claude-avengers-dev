---
name: equip-toolbelt
description: >
  Equip Thor with implementation conventions. Called by Thor via the Skill tool.
  Loads the appropriate toolbelt from equipment/toolbelts/ for the current task.
allowed-tools: Read
argument-hint: "react | python | go | nestjs | laravel"
disable-model-invocation: false
---

# Equip Toolbelt - Thor's Implementation Conventions

## Steps

### 1. Parse Toolbelt Name

Valid toolbelts: `react`, `python`, `go`, `nestjs`, `laravel`.

If no argument or invalid: scan the project root for framework detection:
- `package.json` with "react" or "next" -> `react`
- `package.json` with "nestjs" -> `nestjs`
- `requirements.txt` or `pyproject.toml` -> `python`
- `go.mod` -> `go`
- `artisan` file or `composer.json` with "laravel" -> `laravel`

### 2. Load Toolbelt

Read: `${CLAUDE_PLUGIN_ROOT}/equipment/toolbelts/{toolbelt-name}.md`

### 3. Apply Toolbelt

The toolbelt file is now active context. Follow its conventions and patterns
during implementation. Apply them consistently throughout the task.

Report: "Toolbelt equipped: {toolbelt-name}. Applying conventions to implementation."
