# BMAD Phase 2: PRD (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

| Real skill | Owner | Mode |
| ---------- | ----- | ---- |
| `bmad-prd` (create) | main loop (Vision voice) | interactive |
| optional: `bmad-prd` (validate) and/or `bmad-advanced-elicitation` | main loop (Vision voice) | interactive |

## What happens

`bmad-prd` runs in create mode in the main loop, in Vision's voice, so it can
elicit and validate the product requirements directly with the user (vision,
features, non-goals, MVP scope). It already runs its own reviewer gate.

Afterwards, **offer** — as a plain question — an extra `bmad-prd` validate pass
and/or `bmad-advanced-elicitation` for a deeper critique. Both are optional; skip
them if the user declines. Authoring instructions and completion criteria are
owned by the skills.

See `references/bmad/relay-config.md` for the full phase map.
