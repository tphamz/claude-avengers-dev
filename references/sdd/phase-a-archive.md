# SDD Phase A: Archive + KB (stub)

The last phase on the quick and standard tracks. Main loop.

| Tool | Owner | Mode |
| ---- | ----- | ---- |
| `sdd-openspec.py archive <change>` | main loop | deterministic script |
| `bmad-kb.py impact` → Phase 9 procedure (only when `_bmad/` exists) | main loop (Vision voice) | interactive |
| md commit (`workstation.py md-status`) | main loop, then `Agent(avengers-dev:thor)` | interactive |

## What happens

1. **Archive.** The wrapper refuses a change with no tasks or incomplete tasks
   (OpenSpec's own `archive -y` does not), runs `validate`, then
   `openspec archive <change> -y --json` and reads the result from the JSON — empty
   output, `archive: null` or a `status[]` error is a failure. On success the delta
   specs are merged into `openspec/specs/` and the change moves to
   `openspec/changes/archive/<date>-<change>/`.
   - Incomplete tasks: ask the user. Only with an explicit reason, re-run with
     `--allow-incomplete --reason "<reason>"` and record `archive_override`.
2. **KB (BMAD projects only).** `bmad-kb.py impact --base <kb_base_commit>`, then
   the `/bmad` Phase 9 procedure (`references/bmad/phase-9-kb-refresh.md`). Without
   BMAD, the merged `openspec/specs/` is the refreshed KB.
3. **Commit.** Independent of each other: when `openspec_in_repo` is true
   (`openspec/` is not symlinked into the workstation), Thor commits the
   `openspec/` changes in the code repo as `docs(openspec): archive <change>`; with
   an md workstation, offer the md commit (`/bmad` relay-config §3.13, phase
   `complete`).
4. Set `status: complete`.

See `references/sdd/relay-config.md` for the phase map.
