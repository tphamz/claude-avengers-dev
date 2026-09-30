# BMAD Phase 0: KB Check (stub)

**New in the SDD relay — runs on every track, before anything else.**

| Tool | Owner | Mode | Tracks |
| ---- | ----- | ---- | ------ |
| `skills/bmad/scripts/bmad-kb.py status` | main loop (Vision voice) | deterministic script | all |

## What happens

The script resolves the knowledge base (KB) from `_bmad/bmm/config.yaml` (falling
back to `_bmad/core/config.yaml`, then BMAD defaults):

- `{project_knowledge}/index.md` — written by `bmad-document-project`
- `{output_folder}/project-context.md` — written by `bmad-generate-project-context`

and compares the freshness marker `.avengers/kb.json` against git history. It
prints JSON with a `state`:

| State | Meaning | Relay action |
| ----- | ------- | ------------ |
| `missing` | no `index.md` | run Phase 1a (standard/full); note it on quick |
| `unstamped` | KB present, no marker | offer refresh; if declined, `stamp` and skip 1a |
| `fresh` | no refresh signals since the stamp | skip 1a |
| `stale` | an impact signal, 20+ non-KB files changed, or `unknown_stamp` | show signals, offer refresh (1a) |
| `unknown` | not a git repo | skip 1a, note it; never `stamp` |

`unknown_stamp` is a signal meaning the commit recorded in `.avengers/kb.json` is
no longer in git history (e.g. rebased or squashed away); drift cannot be
measured, so the KB is reported `stale`. In a non-git project `head` is null and
`stamp` exits 1 — skip it.

Record `kb_status_at_start` (the state) and `kb_base_commit` (the `head` value) in
the state file — Phase 9 measures impact from `kb_base_commit`.

Exit codes: 0 = report printed; 1 = `_bmad/` missing. See
`references/bmad/relay-config.md` §3.8 for the KB lifecycle.
