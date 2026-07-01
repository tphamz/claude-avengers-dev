---
name: avengers-log
description: Session audit trail. Shows what was done in this session - files written, commands run, agents dispatched.
allowed-tools: Bash, Read
argument-hint: "[--summary]"
---

# Avengers Log - Session Audit Trail

## Steps

### 1. Summarize Session Activity

Report what happened this session based on visible context:

```
SHIELD Session Log
==================
Session started: {time if known}

Files created or modified:
  + {file1} (created)
  ~ {file2} (modified)

Commands run:
  $ {command1}
  $ {command2}

Agents dispatched:
  → BlackWidow: {task summary}
  → Thor: {task summary}
  → Captain: {verdict}

Skills invoked:
  / avengers-init
  / avengers-test (result: PASS)
```

### 2. If `--summary` flag

Produce a one-paragraph plain English summary suitable for a standup or commit message:
"This session implemented X, explored Y, and reviewed Z. Tests pass."
