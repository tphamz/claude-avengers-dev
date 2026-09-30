# SDD Phase 0: Preflight (stub)

Every run, on the quick and standard tracks. Main loop, deterministic scripts plus
the workstation questions.

| Tool | Owner | Mode |
| ---- | ----- | ---- |
| `sdd-openspec.py preflight` | main loop | deterministic script |
| `workstation.py resolve --link openspec` → `set` / `migrate --link openspec` → `grant-path` | main loop | interactive (the `/avengers-workstation` flow) |
| `sdd-openspec.py init` | main loop | deterministic script |
| `bmad-kb.py status` (only when `_bmad/` exists) | main loop | deterministic script |

## What happens

1. **Preflight.** `openspec` >= 1.13 (on PATH or in `node_modules/.bin`) and git
   >= 2.31. Missing or too old: print the install hint
   (`npm i -g @fission-ai/openspec@latest`) and stop. Avengers never installs it.
2. **md workstation.** As in `/bmad` Step 0 (relay-config §3.11), with the
   `openspec` link: `openspec/` becomes a symlink to `<workstation>/openspec/`. An
   in-repo choice keeps `openspec/` in the repo. A tracked `openspec/` is refused
   with the same untrack warning as `_bmad-output`. Then grant the workstation path.
3. **Init.** Only when `openspec/config.yaml` is missing (or the `avengers-sdd`
   schema is): `openspec init --tools none` — config, `specs/`, `changes/archive/`,
   no `/opsx` commands or skills — plus the `avengers-sdd` schema. A dangling
   `openspec` symlink is refused: re-run the workstation `set`, which creates the
   target first.
4. **KB check (BMAD projects only).** `bmad-kb.py status`: record `head` as
   `kb_base_commit` and report the state. A `missing` or `stale` KB is noted, not
   rebuilt here — suggest `/bmad` if the change needs discovery. Without `_bmad/`,
   the KB is `openspec/specs/` alone; say so once.

See `skills/sdd/SKILL.md` Step 0 for the exit codes and
`references/sdd/relay-config.md` for the phase map.
