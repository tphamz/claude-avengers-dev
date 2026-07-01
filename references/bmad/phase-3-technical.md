# BMAD Phase 3: Architecture (stub)

**Retired self-contained overlay — this phase now wraps the real `bmad-*` skill.**

| Real skill | Owner | Mode |
| ---------- | ----- | ---- |
| `bmad-create-architecture` | main loop (Vision voice) | interactive |

## What happens

`bmad-create-architecture` runs in the main loop, in Vision's voice, producing the
solution/architecture design and recording decisions. It can elicit technical
choices from the user directly. Authoring instructions and completion criteria are
owned by the skill.

See `references/bmad/relay-config.md` for the full phase map.
