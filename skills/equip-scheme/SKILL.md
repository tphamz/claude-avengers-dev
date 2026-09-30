---
name: equip-scheme
description: >
  Equip IronMan with an orchestration scheme. Called by IronMan via the Skill tool.
  Loads the scheme from equipment/schemes/ and follows it for the current initiative.
allowed-tools: Read
argument-hint: "avengers-assemble | rescue-mission | bmad-sequence | sdd-sequence"
disable-model-invocation: false
---

# Equip Scheme - IronMan's Orchestration Workflow

## Steps

### 1. Parse Scheme Name

Valid schemes: `avengers-assemble`, `rescue-mission`, `bmad-sequence`, `sdd-sequence`.

Defaults:
- `avengers-assemble`: standard feature work
- `rescue-mission`: bug fix or incident response
- `bmad-sequence`: full initiative requiring PRD/TDD/backlog
- `sdd-sequence`: a spec-driven change on OpenSpec (`/sdd` quick or standard)

### 2. Load Scheme

Read: `${CLAUDE_PLUGIN_ROOT}/equipment/schemes/{scheme-name}.md`

### 3. Apply Scheme

The scheme is now active context. Follow its phase sequence and crew assignments.
Track which phase is active and announce phase transitions to the user.

Report: "Scheme equipped: {scheme-name}. Following phase sequence."
