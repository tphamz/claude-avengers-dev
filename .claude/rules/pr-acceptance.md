# PR Acceptance Gates

Before creating a PR for the avengers-dev repository, evaluate against this checklist.

## Acceptance Checklist

## Change Categories

- [ ] Agent definitions (`agents/*.md`)
- [ ] Persona (`personas/ironman.md`)
- [ ] Skills (`skills/SKILL.md`)
- [ ] Scripts (`skills/scripts/*.py`)
- [ ] Equipment (`equipment/*/*.md`)
- [ ] Workflow rules (`.claude/rules/*.md`, `CLAUDE.md`)
- [ ] Documentation (`README.md`, etc.)

### Universal Gates

- [ ] Plan mode used and user-approved
- [ ] Hulk reviewed the plan
- [ ] Captain reviewed with verdict: ___
- [ ] Conventional commit messages
- [ ] Atomic scope – one logical change
- [ ] No security vulnerabilities
- [ ] No broken cross-references

### Category-Specific Gates

**Agent Definitions:**

- [ ] Frontmatter valid (name, color, description, tools)
- [ ] Tool list accurate
- [ ] Handoff and failure report templates present

**Skills:**

- [ ] allowed-tools sufficient and minimal
- [ ] Exit codes documented (0/1/2)
- [ ] --dry-run for protected files
- [ ] Debug session validated (CLEAN verdict)

**Scripts:**

- [ ] Stdlib only, argparse, pathlib
- [ ] Exit codes: 0=success, 1=error, 2=no-op
- [ ] --dry-run for protected files
- [ ] Cross-platform (macOS + Linux)

**Equipment:**

- [ ] Equipment file follows existing structure
- [ ] Equip skill branch added

### Severity Summary

- Critical: ___ (all resolved? Y/N)
- Warning: ___ (acknowledged? Y/N)

### Review Cycles

- Cycle count: ___ / 3 max
