---
name: equip-goggles
description: >
  Equip BlackWidow with an exploration strategy. Called by BlackWidow via the Skill tool.
  Loads the appropriate goggles from equipment/goggles/ for the current mission.
allowed-tools: Read
argument-hint: "architecture | detective"
disable-model-invocation: false
---

# Equip Goggles - BlackWidow's Exploration Strategy

## Steps

### 1. Parse Goggles Name

Valid goggles: `architecture`, `detective`.

Default: `architecture` if exploring a codebase for the first time.
Default: `detective` if tracing a bug or specific behavior.

### 2. Load Goggles

Read: `${CLAUDE_PLUGIN_ROOT}/equipment/goggles/{goggles-name}.md`

### 3. Apply Goggles

The goggles file is now active context. Apply its exploration strategy
to the current mission. Structure findings per the goggles' report format.

Report: "Goggles equipped: {goggles-name}. Applying strategy to mission."
