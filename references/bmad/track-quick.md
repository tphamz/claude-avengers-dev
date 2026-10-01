# BMAD Quick Track (stub)

**New in the SDD relay — for small, well-understood changes.** Invoke with
`/avengers-dev:bmad <name> quick`.

| Step | Real skill / tool | Owner | Mode |
| ---- | ----------------- | ----- | ---- |
| 0 KB check | `bmad-kb.py status` | main loop | deterministic script |
| Build | `bmad-quick-dev` | main loop (Vision voice) | interactive |
| Review | diff review | `Agent(avengers-dev:captain)` | autonomous subagent |
| Fix loop | fixes, then re-review (max 3 cycles) | `Agent(avengers-dev:thor)` by default; `bmad-quick-dev` in the main loop only when a fix needs user input; then Captain | as needed |
| Commit check | commit any uncommitted quick-dev work | `Agent(avengers-dev:thor)` | as needed |
| 9 KB Refresh | `bmad-kb.py impact` → refresh → `stamp` | main loop | see Phase 9 |

## What happens

- **Phase 0** runs as usual. A `missing` KB is noted, not built — if the change
  needs discovery, suggest the `standard` track instead.
- **`bmad-quick-dev`** runs in the main loop; it clarifies intent, plans,
  implements, and runs its own step-4 review. That review replaces Captain's
  `bmad-code-review`. **Quick-track exception:** this is the one sanctioned case
  where the main loop writes source code (relay-config `§3.10`).
- **Captain still reviews the diff** — a project rule: every code change is
  reviewed by Captain.
- **Fix loop** — on FAIL, or CONDITIONAL PASS with any `[CRITICAL]`, fix the
  flagged items (Thor by default; re-run `bmad-quick-dev` in the main loop only
  when a fix needs user input) and have Captain re-review. Max 3 cycles, then escalate to the user.
  Advance only on PASS, or CONDITIONAL PASS with no `[CRITICAL]`.
- **Commit before Phase 9** — `bmad-quick-dev` commits its own work when the
  project is a git repo, but not in every case. Phase 9 reads committed history
  only, so any uncommitted work is committed (by Thor) first.
- **Phase 9** evaluates whether the change warrants a KB refresh.

There is no Phase 1b–8 and no design-implementation gate on this track.

See `references/bmad/relay-config.md` for the full phase map.
