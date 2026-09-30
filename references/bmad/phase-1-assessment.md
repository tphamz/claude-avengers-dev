# BMAD Phase 1: Discovery & Brief (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Phase 1 splits in the wrap model:

| Sub-phase | Real skill | Owner | Mode |
| --------- | ---------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` (brownfield) or `bmad-investigate` | main loop; `Agent(avengers-dev:blackwidow)` verifies | interactive + read-only verify |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |

## What happens

- **1a Discovery** — for brownfield (existing code in scope), the main loop runs
  `bmad-document-project` to build project docs under `{project_knowledge}`
  (default `docs/`); use `bmad-investigate` when a specific area needs tracing
  first (case file at
  `{implementation_artifacts}/investigations/{slug}-investigation.md`). Both halt
  for user input and write as they go, so neither runs in a read-only subagent.
  Then resolve the real output paths (relay-config `§2.8`) and dispatch
  BlackWidow read-only to verify them against the codebase. Greenfield with no
  code: skip 1a and note it in the state file.
- **1b Brief** — `bmad-product-brief` runs in the main loop so it can elicit the
  problem, users, success criteria, and non-goals from the user.

Authoring instructions and completion criteria are owned by those skills. See
`references/bmad/relay-config.md` for the full phase map and the state schema.
