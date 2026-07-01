# BMAD Phase 1: Discovery & Brief (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Phase 1 splits in the wrap model:

| Sub-phase | Real skill | Owner | Mode |
| --------- | ---------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` (brownfield) or `bmad-investigate` | `Agent(avengers-dev:blackwidow)` | autonomous subagent |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |

## What happens

- **1a Discovery** — for brownfield (existing code in scope), BlackWidow runs
  `bmad-document-project` to build project context; use `bmad-investigate` when a
  specific area needs tracing first. Greenfield with no code: skip 1a and note it
  in the state file.
- **1b Brief** — `bmad-product-brief` runs in the main loop so it can elicit the
  problem, users, success criteria, and non-goals from the user.

Authoring instructions and completion criteria are owned by those skills. See
`references/bmad/relay-config.md` for the full phase map and the state schema.
