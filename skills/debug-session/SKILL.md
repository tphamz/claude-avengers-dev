---
name: debug-session
description: >
  Analyze a Claude Code --debug log after skill testing. Produces a verdict:
  CLEAN, PARTIAL, or FAILED with specific error details.
allowed-tools: Bash, Read, Glob
argument-hint: "[log-file-path]"
---

# Debug Session - Analyze Debug Log

## Steps

### 1. Find the Log File

**If argument provided:** Use that path directly.

**If no argument:**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/debug-session/scripts/resolve-debug-log.py
```

Exit 0: prints path to most recent debug log.
Exit 1: no log found - instruct user to run claude with `--debug` flag.

### 2. Parse the Log

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/debug-session/scripts/parse-debug-log.py \
  --log-file {path}
```

Output is JSON with:
- `bash_errors`: list of Bash tool errors from our scripts
- `permission_prompts`: list of permission prompts triggered
- `write_failures`: list of Write/Edit tool failures
- `skill_invocations`: list of skills invoked
- `agents_dispatched`: list of Agent() calls
- `files_written`: list of files created or modified

### 3. Produce Verdict

**CLEAN:** Zero bash errors, zero permission prompts, zero write failures. All expected files present.

**PARTIAL:** Some issues but core functionality worked. List specific failures.

**FAILED:** Critical errors that prevented the skill from completing.

### 4. Report

```
Debug Session Analysis
======================
Log: {path}
Session: {timestamp if found}

Skills invoked: {list}
Agents dispatched: {list}
Files written: {count}

Issues found:
  ✗ Bash error in avengers-init.py: [error message]
  ⚠ Permission prompt: Write to .claude/settings.local.json

VERDICT: PARTIAL

Fix required: [specific actionable guidance]
```
