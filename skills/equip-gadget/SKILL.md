---
name: equip-gadget
description: >
  Equip Hulk with a domain review gadget. Called by Hulk via the Skill tool.
  Loads the appropriate gadget from equipment/gadgets/ for the current review.
allowed-tools: Read
argument-hint: "deployment | compliance"
disable-model-invocation: false
---

# Equip Gadget - Hulk's Domain Review

## Steps

### 1. Parse Gadget Name

Valid gadgets: `deployment`, `compliance`.

Default: `deployment` if reviewing a plan that involves shipping code.
Default: `compliance` if the task involves handling user data, payments, or regulated domains.

### 2. Load Gadget

Read: `${CLAUDE_PLUGIN_ROOT}/equipment/gadgets/{gadget-name}.md`

### 3. Apply Gadget

The gadget file is now active context. Apply its criteria and checklist
to the current plan review. Integrate gadget findings into Hulk's Engineering Review.

Report: "Gadget equipped: {gadget-name}. Applying criteria to review."
