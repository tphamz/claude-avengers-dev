# Git Workflow - Avengers Dev Standard

## Branch Naming

```
feature/{ticket-or-description}
fix/{ticket-or-description}
chore/{ticket-or-description}
docs/{ticket-or-description}
```

## Commit Format (Conventional Commits)

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `style`, `perf`, `ci`

Examples:
- `feat(auth): add OAuth2 provider support`
- `fix(payments): handle network timeout on retry`
- `chore(deps): upgrade to React 19`

## Pre-Commit Checks

Before every commit:
1. Run the test suite (`make test` or framework-appropriate command)
2. Scan for secrets: `git diff --staged | grep -i 'password\|secret\|api_key\|token'`
3. Check for `.env` files in staging: `git diff --staged --name-only | grep '\.env'`
4. Verify all files in staging are intentional

## PR Requirements

- Title follows conventional commit format
- Description explains WHY, not just what
- Tests pass in CI
- Captain has reviewed
- No security vulnerabilities

## Commit Scope

Atomic commits. One logical change per commit. If you can't summarize in 50 characters, split the commit.
