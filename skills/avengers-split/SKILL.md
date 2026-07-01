---
name: avengers-split
description: Quick project health check. Scans for obvious issues - broken imports, missing env vars, common misconfigurations.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: "[--fix]"
---

# Avengers Split - Project Health Check

## Steps

### 1. Detect Project Type

Identify from project files: Node.js, Python, Go, Ruby, PHP, Rust.

### 2. Run Health Checks

#### Node.js projects
- `node_modules/` exists (if not: "Run npm install")
- `package.json` has `scripts.test` defined
- `.env.example` exists if `.env` is referenced in code
- No `console.log` in non-test files (warn, not error)

#### Python projects
- Virtual environment exists (`venv/`, `.venv/`, or `poetry.lock`)
- `requirements.txt` or `pyproject.toml` exists
- No unused imports (run `python -m py_compile` on `*.py` files)

#### Go projects
- `go.mod` present
- `go.sum` present (if dependencies exist)
- No unused imports (run `go build ./...`)

#### All projects
- `.gitignore` exists
- No `.env` files committed (check `git ls-files | grep .env`)
- No large binary files (>10MB) tracked in git

### 3. Report Results

```
SHIELD Health Report
====================
Project: [name]
Type: [detected type]

✓ Dependencies installed
✓ Test script configured
⚠ Missing .env.example (referenced in 3 files)
✗ .env committed to git! Remove immediately.

Summary: 1 critical, 1 warning, 2 passing
```

### 4. If `--fix` flag provided

Attempt safe auto-fixes:
- Add `.env` to `.gitignore` (if not present)
- Create `.env.example` from `.env` (with values redacted)
- Do NOT auto-fix anything that modifies existing code
