# SDD Phase B: Build (stub)

Quick and standard tracks. One Thor dispatch per change (re-dispatched in the fix
loop).

| Procedure | Owner | Mode |
| --------- | ----- | ---- |
| tests first (standard), then `tasks.md` in order | `Agent(avengers-dev:thor)` | autonomous subagent |

## What happens

Thor gets the change id, the track, and the `sdd-openspec.py status` JSON. He reads
the artifacts under `change_dir_real` (and may run `sdd-openspec.py instructions
apply <change>` for `contextFiles` and progress). He never runs `openspec` directly.

- **Standard (tests first):** write every test listed in `tests.md`, run them with
  its `## Run` command, and confirm each FAILS for the right reason (an assertion,
  not a syntax or import error). Tick each in `tests.md`. Only then work through
  `tasks.md`.
- **Both tracks:** work `tasks.md` top to bottom; tick `- [x]` as each task's stated
  verification passes. Run the project's tests. Commit the code with a
  conventional message. When `openspec_in_repo` is true, include the
  `openspec/changes/<id>/` updates in the commit; otherwise the change files live
  in the workstation and are covered by the md commit.
- **Scope creep** (`/bmad` relay-config §3.7): an out-of-scope requirement is
  reported, not built.

Thor reports the test results, the ticked tasks, and the commit.

See `references/sdd/relay-config.md` for the phase map.
