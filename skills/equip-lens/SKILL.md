---
name: equip-lens
description: >
  Equip Captain America with a review lens. Called by Captain via the Skill tool.
  Loads the appropriate lens from equipment/lenses/ and applies it to the current review.
allowed-tools: Read
argument-hint: "security | performance | ui-ux | adversarial"
disable-model-invocation: false
---

# Equip Lens - Captain's Review Focus

## Steps

### 1. Parse Lens Name

The argument is the lens name. Valid lenses: `security`, `performance`, `ui-ux`, `adversarial`.

If no argument or invalid argument: default to `security`.

### 2. Load Lens

Read: `${CLAUDE_PLUGIN_ROOT}/equipment/lenses/{lens-name}.md`

### 3. Apply Lens

The lens file is now active context. Apply its checklist and criteria to the
current code review. The lens supplements (does not replace) Captain's standard review.

Report: "Lens equipped: {lens-name}. Applying criteria to review."
