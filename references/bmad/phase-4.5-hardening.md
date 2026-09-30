# BMAD Phase 4.5: Spec Hardening (stub)

**New in the SDD relay — wraps the real `bmad-*` review skills.** Standard and full
tracks.

| Real skill(s) | Owner | Mode |
| ------------- | ----- | ---- |
| `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | main loop; `Agent(avengers-dev:captain)` (`adversarial` lens) verifies | interactive + read-only verify |
| applying fixes | main loop (Vision voice) | interactive |

## What happens

The main loop runs both review skills over the epics, stories, and acceptance
criteria (ACs) from Phase 4, checking that every AC is concrete, independently
testable, and covers error and edge paths (every wrapped skill runs in the main
loop, relay-config `§3.12`). Then it resolves the story paths (relay-config
`§2.8`) and dispatches Captain read-only, with the `adversarial` lens, those paths
and both skills' findings, to verify them (no test gate: this is a
pre-implementation spec review, so Captain skips his Step 1 test run;
`agents/captain.md` Hardening Verification (/bmad 4.5, /sdd H)).

**Captain assigns the severity tags** — `[CRITICAL]` / `[WARNING]` /
`[SUGGESTION]` — because the wrapped skills emit findings without severity.

Captain reports only. Back in the main loop, walk the findings with the user and
apply the agreed fixes to the stories. Any `[CRITICAL]` left unresolved is carried
to the Phase 5 → 6 gate, where passing requires an `override` with a reason
(relay-config §3.11).

See `references/bmad/relay-config.md` for the full phase map.
