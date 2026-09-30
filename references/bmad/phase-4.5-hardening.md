# BMAD Phase 4.5: Spec Hardening (stub)

**New in the SDD relay — wraps the real `bmad-*` review skills.** Standard and full
tracks.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | `Agent(avengers-dev:captain)`, `adversarial` lens | autonomous subagent |
| applying fixes | main loop (Vision voice) | interactive |

## What happens

Captain runs both review skills over the epics, stories, and acceptance criteria
(ACs) from Phase 4, checking that every AC is concrete, independently testable, and
covers error and edge paths.

**Captain assigns the severity tags** — `[CRITICAL]` / `[WARNING]` /
`[SUGGESTION]` — because the wrapped skills emit findings without severity.

Captain reports only. Back in the main loop, walk the findings with the user and
apply the agreed fixes to the stories. Any `[CRITICAL]` left unresolved is carried
to the Phase 5 → 6 gate, where passing requires an `override` with a reason
(relay-config §3.9).

See `references/bmad/relay-config.md` for the full phase map.
