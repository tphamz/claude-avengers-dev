# BMAD Phase 1: Discovery & Brief (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skills.**

Phase 1 splits in the wrap model. Both sub-phases run in the **main loop**: the
wrapped skills are interactive, and a subagent cannot elicit from the user.

| Sub-phase | Real skill | Owner | Mode |
| --------- | ---------- | ----- | ---- |
| 1a Discovery (conditional) | `bmad-document-project` + `bmad-generate-project-context`, then `bmad-kb.py stamp` | main loop (Vision voice) | interactive |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |

## What happens

- **1a Discovery** — runs only when Phase 0 reports the KB `missing`, or `stale` /
  `unstamped` and the user accepts a refresh. `bmad-document-project` builds the
  KB index (`initial_scan` when missing, `full_rescan` when refreshing), then
  `bmad-generate-project-context` writes the AI-rules context file, then
  `bmad-kb.py stamp` records the freshness marker. Greenfield with no code: skip
  1a and note it in the state file.
- **1b Brief** — `bmad-product-brief` runs in the main loop so it can elicit the
  problem, users, success criteria, and non-goals from the user.

Authoring instructions and completion criteria are owned by those skills. See
`references/bmad/relay-config.md` for the full phase map, the state schema, and
§3.8 for the KB lifecycle.
