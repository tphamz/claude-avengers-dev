---
name: git-workflow
description: >
  Enable or disable custom git workflow instructions for this project.
  The git workflow enforces conventional commits, branch naming, and pre-commit checks.
allowed-tools: Bash, Read, Write
argument-hint: "enable | disable"
---

# Git Workflow - Custom Git Instructions

## Commands

### `enable`

Adds git workflow instructions to `.claude/settings.local.json`:

Read the workflow instructions from:
`${CLAUDE_PLUGIN_ROOT}/skills/git-workflow/git-workflow.md`

Add to `.claude/settings.local.json` under `bashDirectives`:
```json
{
  "bashDirectives": [
    "Before any git commit: run tests, check for secrets, use conventional commit format."
  ]
}
```

Also copies `skills/git-workflow/git-workflow.md` to `.claude/rules/git-workflow.md`
so Claude auto-loads the full workflow on session start.

### `disable`

Removes `.claude/rules/git-workflow.md`.

Report: "Git workflow disabled for this project."

## Exit Codes

- 0: success
- 1: error
- 2: no-op (already enabled/disabled)
