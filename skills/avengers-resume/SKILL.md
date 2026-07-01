---
name: avengers-resume
description: Restore from a checkpoint saved with /avengers-checkpoint. Lists available checkpoints or restores a specific one.
allowed-tools: Bash, Read, Glob
argument-hint: "[checkpoint-name]"
---

# Avengers Resume - Restore from Checkpoint

## Steps

### 1. List or Load

**If no argument provided:** List available checkpoints.

```bash
ls .avengers/checkpoints/*.json 2>/dev/null
```

Display each with: name, captured_at, git branch from the JSON.

**If argument provided:** Load that checkpoint.

### 2. Display Checkpoint State

Read the checkpoint JSON and display:

```
Checkpoint: {name}
Captured: {timestamp} ({time-ago})

Git State:
  Branch: {branch}
  Status: {status summary}
  Recent commits:
    - {commit1}
    - {commit2}
    - {commit3}

Active relay sequences: {list or "none"}
Notes: {notes or "none"}
```

### 3. Context Restoration

After displaying, say:
> "Checkpoint loaded. Review the state above. What would you like to resume?"

Do NOT automatically start doing things. The user decides what to resume.
