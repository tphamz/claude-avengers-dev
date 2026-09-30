# SDD Quick Track (stub)

For small, well-understood changes. Invoke with `/avengers-dev:sdd <name> quick`.
OpenSpec's built-in `spec-driven` schema; no Harden, Readiness or gate.

| Step | Tool / procedure | Owner | Mode |
| ---- | ---------------- | ----- | ---- |
| 0 Preflight | `sdd-openspec.py preflight` → workstation → `init` → KB check (BMAD only) | main loop | scripts + questions |
| P Propose (lite) | `new --schema spec-driven` → `instructions` per artifact | main loop (Vision voice) | interactive |
| B Build | `tasks.md` in order | `Agent(avengers-dev:thor)` | autonomous subagent |
| V Verify + review | `references/sdd/verify.md` + code review; fix loop max 3 | `Agent(avengers-dev:captain)` | autonomous subagent |
| A Archive + KB | `sdd-openspec.py archive` → `bmad-kb.py impact` (BMAD only) → md commit | main loop | scripts + questions |

## What happens

- **Propose (lite):** short proposal and delta specs, `design.md` only when the
  instruction's own criteria call for one, and tasks. One confirmation at the end
  instead of one per artifact.
- **Build** and **Verify** as on the standard track, without the tests-first step.
  Captain still reviews every change — a project rule.
- **Archive** is guarded as on every track.

There is no design-implementation gate on this track.

See `references/sdd/relay-config.md` for the full phase map.
