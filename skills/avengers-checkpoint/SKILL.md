---
name: avengers-checkpoint
description: Save current pipeline state to a checkpoint file. Captures current task context, in-progress work, and next steps.
allowed-tools: Bash, Read, Write
argument-hint: "[checkpoint-name]"
---

# Avengers Checkpoint - Save Pipeline State

## Steps

### 1. Determine Checkpoint Path

- If argument provided: `.avengers/checkpoints/{argument}.json`
- Otherwise: `.avengers/checkpoints/checkpoint-{ISO-timestamp}.json`

Create `.avengers/checkpoints/` directory if it doesn't exist.

### 2. Collect State

Gather:
- Current timestamp (ISO 8601)
- Current working directory
- Git branch (if in git repo): `git rev-parse --abbrev-ref HEAD`
- Git status summary: `git status --short`
- Last 3 git commits: `git log --oneline -3`
- Any active `.avengers/relay-sequences/*.yaml` files

### 3. Write Checkpoint

Write JSON to the checkpoint path:

```json
{
  "checkpoint_id": "{name or timestamp}",
  "captured_at": "{ISO timestamp}",
  "git": {
    "branch": "{branch}",
    "status": "{git status output}",
    "recent_commits": ["{commit1}", "{commit2}", "{commit3}"]
  },
  "relay_sequences": ["{list of active .yaml files}"],
  "notes": "{any notes provided by user}"
}
```

### 4. Confirm

Report: `Checkpoint saved: .avengers/checkpoints/{name}.json`
