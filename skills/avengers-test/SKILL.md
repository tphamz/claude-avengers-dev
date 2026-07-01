---
name: avengers-test
description: >
  Auto-detects the project's test framework, runs the test suite, and reports
  with Avengers-themed output. Supports Jest, Vitest, pytest, Go test, RSpec,
  Mocha, and Cargo test.
allowed-tools: Bash, Read, Grep, Glob
---

# Avengers Test - Powered Test Runner

## Steps

### 0. Check for Makefile (Priority)

If `make test` target exists, run `make test`. Only proceed to auto-detection if not.

### 1. Detect Test Framework

| Framework  | Detection                                                          |
| ---------- | ------------------------------------------------------------------ |
| Jest       | `jest.config.*`, `"jest"` in `package.json`                        |
| Vitest     | `vitest.config.*`, `"vitest"` in `package.json`                    |
| pytest     | `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, `conftest.py` |
| Go test    | `go.mod` with `*_test.go` files                                    |
| RSpec      | `.rspec`, `spec/` directory with `Gemfile` containing `rspec`      |
| Mocha      | `.mocharc.*`, `"mocha"` in `package.json`                          |
| Cargo test | `Cargo.toml` with `#[test]` in `*.rs` files                        |

### 2. Run Tests

- **Jest**: `npx jest --verbose --no-coverage`
- **Vitest**: `npx vitest run --reporter=verbose`
- **pytest**: `python -m pytest -v`
- **Go test**: `go test ./... -v`
- **RSpec**: `bundle exec rspec --format documentation`
- **Mocha**: `npx mocha --reporter spec`
- **Cargo test**: `cargo test --nocapture`

### 3. Parse Results

Extract: total tests, passed, failed, skipped, time, coverage if available.

### 4. Report Results

**All tests pass:**
```

AVENGERS ASSEMBLED! All tests passed!
Passed: XX | Failed: 0 | Skipped: XX | Time: X.XXs
Worthy code!

```

**Some tests fail:**
```

Code Red! Test failures detected!
Passed: XX | Failed: XX | Skipped: XX | Time: X.XXs
Failed Tests:

- [test name]: [brief reason]
  Root Cause Analysis: [grouped by likely cause]
  Suggestions: [actionable steps]
  Even heroes stumble. Let's fix this.

```

**No tests found:**
```

No tests found. Consider setting up: [suggested framework based on project type]

```
