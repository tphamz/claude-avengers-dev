# BMAD Phase 9: KB Refresh (stub)

**New in the SDD relay — the last phase on every track.** Phase 8 (or the quick
track's review) advances here instead of setting `complete`.

| Real skill(s) / tool | Owner | Mode |
| -------------------- | ----- | ---- |
| `bmad-kb.py impact --base <kb_base_commit>` | main loop | deterministic script |
| `bmad-document-project` (`deep_dive` / `full_rescan`) + `bmad-generate-project-context` | main loop (Vision voice) | interactive |
| `bmad-kb.py stamp` | main loop | deterministic script |

## What happens

1. Run `impact --base <kb_base_commit>`. It reports `refresh_recommended`, the
   `signals` (breaking-change commits, architecture doc changes, dependency
   manifests, migrations, API contracts, new top-level dirs, 20+ changed files),
   and `changed_areas`. Exit 2 (no commits since base) → set `complete`.
2. If `refresh_recommended`, show the signals and ask the user to confirm.
3. On confirm: 3 or fewer `changed_areas` → `bmad-document-project` in `deep_dive`
   once per area; otherwise `full_rescan`.
4. `bmad-generate-project-context` updates `{output_folder}/project-context.md`.
5. `stamp` (writes this branch's entry in the marker — `<workstation>/avengers/kb.json`
   with an md workstation, else `.avengers/kb.json` — and refreshes
   `.claude/rules/avengers-kb.md` — search hint plus the `project-context.md` import),
   then set `status: complete`.
6. No refresh recommended, or the user declines → set `complete` directly.

**Resume defaults** apply only to a **legacy state file** — one with no `track`
key. A legacy sequence already at `8` or `complete` is not routed into Phase 9;
any other legacy sequence reaches Phase 9 and, with no `kb_base_commit`, uses the
`stamped_commit` from `bmad-kb.py status`, or skips Phase 9 with a note if there
is none.
State files with a `track` key always go through Phase 9.

**Not a git repo:** `impact` exits 1; note it and set `complete` (no `stamp`).

With an md workstation, offer an md commit (relay-config §3.11) before announcing
completion.

See `references/bmad/relay-config.md` §3.8 for the KB lifecycle.
