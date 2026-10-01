# Agents: replace mid-run agent messaging with stop-and-ask

## Objective
Thor and BlackWidow described a two-tier "get help mid-run" scheme that relied on
messaging BlackWidow or IronMan. Subagents have no Agent or SendMessage tool, so an
agent following it stalls or invents a channel. Replace it with one path: self-serve
lookups, otherwise stop and return a question; IronMan answers and re-dispatches with
the answer, Work state and Resume instruction (the same mechanism as `/bmad` §3.12
step 4).

## Scope

**Files to Create/Modify/Delete**
- `agents/thor.md` — rewrite `## Getting Help Mid-Implementation` as self-serve then stop-and-ask with the Blocked Report, with one Blocked-vs-Stuck sentence; widen the generic Blocked variant to stops that need IronMan or the user, adding research and plan-change questions (`Skill: n/a (question)`); rewrite the Tier 1 catchphrase
- `agents/blackwidow.md` — replace `## Helping Teammates` with `## When the Question Grows` (keeps the 5+ files threshold)
- `personas/ironman.md` — delete the "communicate directly on Tier 1 lookups" line; add `### Questions From Agents` under `## How You Work`
- `.claude/rules/ironman-delegation.md` — delegation row for a returned question, and a note that a Stuck report without a question uses the failure row
- `tests/test_doc_consistency.py` — checker for mid-run agent messaging over tracked instruction docs, plus a mutation test
- `specs/stories/agent-escalation-path.md` — this spec

## Design & Structure
Documentation change in the existing agent, persona and rule formats; no new report
template (the generic Blocked Report and the If You Get Stuck report carry the
question). The checker follows the module's pure checker plus real-file test plus
mutation test pattern and scans `tracked_markdown()` under `agents/`, `personas/`,
`equipment/`, `skills/`, `references/`, `.claude/rules/`, `CLAUDE.md` and `README.md`.

## Acceptance Criteria
- [ ] No in-scope doc matches `\b(message|messages|ask|asks|ping|contact)\s+(ironman|tony|blackwidow|black widow|thor|captain|hulk|vision)\b|communicate directly` (case-insensitive), and a test enforces it
- [ ] A mutation test proves a reintroduced messaging line is reported
- [ ] Thor's generic Blocked variant covers stops that need IronMan or the user, including research and plan-change questions
- [ ] Blocked (needs an answer, work preserved) and Stuck (failed) are distinguished
- [ ] IronMan's persona and the delegation rule re-dispatch with answer + Work state + Resume instruction; a Stuck report without a question uses the failure row
- [ ] The `**Design standard.**` paragraph, `/bmad`, `/sdd` and relay-config text are unchanged
- [ ] `python3 -m unittest discover -s tests` passes

## Tasks
- [ ] Edit thor.md, blackwidow.md, the persona and the delegation rule
- [ ] Add the messaging checker and tests
- [ ] Run the tests and commit `fix(agents): replace mid-run agent messaging with stop-and-ask`; do not push

## Engineering Notes (Hulk)
- Widen the generic Blocked scope from "needs the user" to "needs input from IronMan or the user".
- Blocked means "need an answer"; Stuck means "failed". The delegation row keys on whether the report carries a question.
- The test pattern is broadened beyond the four removed lines, has no `Tier` term (`phase-8-review.md` uses "Tier 1" for code-review tiers), and scans repo-wide through `tracked_markdown()`, excluding `specs/` and `tests/`.
- No SendMessage path: resuming a finished subagent is unverified, so re-dispatch is the single path.
- The persona rule lives under `## How You Work`, next to the Quality Gate and Closure Loop rules.
- BlackWidow keeps the 5+ files threshold.

## Status
- [x] Spec approved by user
