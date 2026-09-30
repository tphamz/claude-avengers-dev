# SDD Phase P: Propose (stub)

Main loop, Vision's voice. Quick track (lite) and standard track.

| Tool | Owner | Mode |
| ---- | ----- | ---- |
| `sdd-openspec.py new <change> --schema S` | main loop | deterministic script |
| `sdd-openspec.py instructions <artifact> <change>` → write the artifact | main loop (Vision voice) | interactive |
| `sdd-openspec.py status <change>` | main loop | deterministic script |

## What happens

1. Create the change with its schema pinned: `spec-driven` (quick) or
   `avengers-sdd` (standard). The change id is kebab-case; it defaults to the
   sequence name.
2. Loop while `status` reports a `next` artifact: fetch its instructions (the JSON
   has `instruction`, `template`, `resolvedOutputPath` and `dependencies`), draft it
   with the user, and write it to `resolvedOutputPath`. Ask rather than guess when
   an answer would change the specs, the approach or the task breakdown.
   - **Standard:** proposal → specs → design → tests → tasks, each confirmed with
     the user (relay-config §3.5).
   - **Quick (lite):** proposal and specs short; `design.md` always (the
     `spec-driven` schema's `tasks` requires it) — one line, `Not needed: <reason>`,
     when the change needs no design; tasks. One confirmation at the end.
   - **Loop guard:** re-run `status` after each write. If `next` has not moved
     past the artifact just written, stop and report it with the path and the
     `status` JSON instead of looping.
3. Delta specs: `## ADDED` / `## MODIFIED` / `## REMOVED` / `## RENAMED
   Requirements`, each requirement with at least one `#### Scenario:` in WHEN/THEN
   form. For MODIFIED, copy the whole existing requirement from
   `openspec/specs/<capability>/spec.md` and edit it.
4. Done when `status` reports `planning_complete: true` (`next` is `apply`).

See `references/sdd/relay-config.md` for the phase map.
