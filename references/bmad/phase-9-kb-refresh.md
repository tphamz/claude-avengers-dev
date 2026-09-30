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
5. `stamp`, then set `status: complete`.
6. No refresh recommended, or the user declines → set `complete` directly.

**Resume defaults:** a missing `kb_base_commit` falls back to the commit in
`.avengers/kb.json`, or Phase 9 is skipped with a note. A sequence already at `8`
or `complete` from before this phase existed is never routed into Phase 9.

See `references/bmad/relay-config.md` §3.8 for the KB lifecycle.
