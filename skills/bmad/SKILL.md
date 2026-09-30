---
name: bmad
description: >
  Initiate or resume a BMAD sequence as a spec-driven relay over the real
  BMAD-METHOD `bmad-*` skills, in Vision's voice. Three tracks — quick, standard,
  full — with a knowledge-base (KB) lifecycle (build when missing, refresh when
  stale or after impactful changes), spec hardening before the gate, and
  ATDD + requirement-to-test trace on the full track. Interactive skills run in
  the main loop; non-interactive phases are delegated to Hulk, Thor, and Captain.
  IronMan holds the design-implementation hard gate.
allowed-tools: Skill, Agent, Bash, Read, Write
argument-hint: "[sequence-name] [quick|standard|full|resume]"
---

# BMAD — Conducting the Real BMAD-METHOD

This skill does **not** reimplement BMAD. It **wraps** the installed BMAD-METHOD
`bmad-*` skills and orchestrates them through the Avengers crew, narrating each
transition in **Vision's** voice. Vision is the conductor and the phase→skill+owner
map — not a subagent (a subagent runs blind and cannot elicit from the user, so
every interactive skill must run in this main loop).

**IronMan's job here:** run the sequence, speak in Vision's voice at each phase
boundary, dispatch the owning Avenger for delegated phases, and hold the
design-implementation hard gate (Phase 5 → 6).

The KB helper script is `${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py`
(referred to below as **bmad-kb.py**). Every subcommand accepts `--project-dir`
(default: current directory) and prints `--help`.

## Ownership Map — phase → real skill → owner → tracks

| Phase | Real skill(s) invoked | Owner | Tracks |
| ----- | --------------------- | ----- | ------ |
| 0 KB check | `bmad-kb.py status` | main loop | all |
| 1a Discovery (KB `missing`, or `stale` and user accepts) | `bmad-document-project` + `bmad-generate-project-context`, then `bmad-kb.py stamp` | main loop (Vision voice) | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` (create); optional `bmad-prd` validate / `bmad-advanced-elicitation` | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | `Agent(avengers-dev:captain)`, `adversarial` lens; fixes in main loop | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | standard, full |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full only) → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full only) + `bmad-retrospective` | `Agent(avengers-dev:captain)` | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → `bmad-document-project` + `bmad-generate-project-context` → `bmad-kb.py stamp` | main loop (Vision voice) | all |
| Quick track | `bmad-quick-dev`, then Captain reviews the diff | main loop, then `Agent(avengers-dev:captain)` | quick |

<!-- SEAM: Phases 1a–4 are interactive today because the real bmad-* skills elicit
     from the user, and a subagent cannot elicit. If those skills later gain a
     non-interactive / batch mode, these phases can be flipped to a fully-autonomous
     Vision subagent by moving their rows to "Agent(avengers-dev:vision)". Do not
     flip them while the wrapped skills still ask the user questions. -->

## Tracks

| Track | Phases | Use when |
| ----- | ------ | -------- |
| `quick` | 0 → quick-dev → Captain diff review → 9 | small, well-understood change; no PRD/architecture needed |
| `standard` | 0 → 1a (conditional) → 1b → 2 → 3 → 4 → 4.5 → 5 → gate → 6 → 7 → 8 → 9 | default for features and initiatives |
| `full` | as standard, plus ATDD in 7 and trace in 8 | acceptance tests must be written first and traced to ACs; needs the TEA module |

## Steps

> **Prompting (avoid "Invalid tool parameters"):** every user-facing question in
> this skill — the sequence name, the track, the resume choice, the stale-KB
> refresh offer, the Phase 5→6 [1]/[2] gate, and the Phase 9 refresh confirmation —
> is a **plain conversational question**. Ask it directly in the chat in Vision's
> voice and wait for the user's reply. Do **NOT** use a structured
> question/elicitation tool for these prompts; a plain text question has no schema
> to malform.

### 0. Preflight — BMAD-METHOD dependency check

Each wrapped `bmad-*` skill expects a **project-level install** at
`{project-root}/_bmad/`, created by `npx bmad-method install`. Before anything
else, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py preflight
```

Exit 0 (prints `BMAD_OK`): continue to Step 1. Exit 1 (prints `BMAD_MISSING`):
**STOP** — do not parse args, create a state file, or begin a sequence. Announce,
in Vision's voice, then exit:

> 🔴 Vision — online. "BMAD-METHOD is not installed in this project. I conduct the
> real framework — it needs its project config first. Run `npx bmad-method install`
> in this directory, then re-run `/avengers-dev:bmad`."

Once the track is known (Step 1) and it is `full`, run preflight again with
`--track full`. Exit 2 (prints `TEA_MISSING`) means `_bmad/tea/` is absent. There
is no silent fallback: ask the user to choose **[a] downgrade to `standard`** or
**[b] stop** and run `npx bmad-method install` to add the TEA module (with a test
framework configured, e.g. via `bmad-testarch-framework`). Record the choice.

### 1. Parse Arguments

- **No argument**: prompt for a sequence name (kebab-case, descriptive — e.g.
  "payment-gateway", "auth-modernization"), then ask for the track.
- **`[sequence-name]`**: new sequence with that name; ask for the track, suggesting
  `standard` as the default.
- **`[sequence-name] quick|standard|full`**: new sequence on that track.
- **`[sequence-name] resume`** or **`resume [sequence-name]`**: resume an existing sequence.
- **`resume`** (no name): list available sequences and prompt for selection.

### 2. Check for / Resume an Existing Sequence

Look for state files matching `.avengers/relay-sequences/bmad-*.yaml`. If one
matching the name exists, ask (in Vision's voice):
"A BMAD sequence named '{name}' already exists. Resume it?"

On resume: read `.avengers/relay-sequences/bmad-{name}.yaml`, apply the
**resume defaults** for older state files (relay-config §3.2):

- missing `track` → `standard`
- missing `kb_base_commit` → Phase 9 uses the commit in `.avengers/kb.json`, or is
  skipped with a note if there is none
- a sequence already at `8` or `complete` is never routed into Phase 9

then announce
> 🔴 Vision — online. "Resuming BMAD '{name}' ({track}) at Phase {N}: {phase-name}."
and re-enter at `current_phase` (respecting `design_implementation_boundary_passed`).

On a new sequence: create the state file with `current_phase: 0`, `track`,
`status: active`, `design_implementation_boundary_passed: false`,
`gate_override: null`. Schema reference:
`${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md`.

### 3. Run the Phase Sequence

Open every phase transition with the Vision identity header + a matching
catchphrase (see `agents/vision.md`), then execute the phase per its owner:

- **Main-loop phases (0, 1a, 1b, 2, 3, 4, 6, 9, quick-dev)** — invoke the real
  skill **in this main loop** with `Skill(bmad-X)` so it can elicit from the user
  directly. Confirm the phase boundary with the user before advancing (§3.5).
- **Delegated phases (4.5, 5, 7, 8)** — dispatch the owning Avenger with
  `Agent(avengers-dev:owner)`, instructing it to run the named real skill
  autonomously and report back. Relay the result in that agent's voice.

Phase-by-phase (standard and full tracks; quick track is Step 6):

1. **Phase 0 — KB check.** Run `bmad-kb.py status` (exit 0: JSON on stdout; exit 1:
   `_bmad/` missing — stop as in Step 0). Record `state` as `kb_status_at_start`
   and the `head` value as `kb_base_commit`.
   - `missing` → run Phase 1a.
   - `stale` → show the `signals` and offer a refresh; run 1a only if the user accepts.
   - `unstamped` → the KB exists but its age is unknown; offer a refresh as for
     `stale`. If declined, run `bmad-kb.py stamp` so later runs can measure drift,
     and skip 1a.
   - `fresh` or `unknown` → skip 1a (note `unknown` = not a git repo).
2. **Phase 1a — Discovery (main loop).** `Skill(bmad-document-project)` —
   `initial_scan` when missing, `full_rescan` when refreshing a stale KB — then
   `Skill(bmad-generate-project-context)`, then `bmad-kb.py stamp` (exit 0 stamped;
   exit 2 already stamped at HEAD, fine; exit 1 error, report it). Greenfield with
   no code: skip 1a and note it in the state file.
3. **Phase 1b — Brief.** `Skill(bmad-product-brief)`.
4. **Phase 2 — PRD.** `Skill(bmad-prd)` in create mode (it runs its own reviewer
   gate). Then **offer**, as a plain question, an optional `bmad-prd` validate pass
   and/or `Skill(bmad-advanced-elicitation)`. Skip both if the user declines.
5. **Phase 3 — Architecture.** `Skill(bmad-create-architecture)`.
6. **Phase 4 — Epics & Stories.** `Skill(bmad-create-epics-and-stories)`.
7. **Phase 4.5 — Spec Hardening.** Dispatch `Agent(avengers-dev:captain)` with the
   `adversarial` lens to run `bmad-review-adversarial-general` and
   `bmad-review-edge-case-hunter` over the stories and acceptance criteria (ACs),
   checking every AC is testable. **Captain assigns the
   `[CRITICAL]`/`[WARNING]`/`[SUGGESTION]` tags** — the wrapped skills emit no
   severity. Captain reports only; back in the main loop, walk the findings with
   the user and apply the agreed fixes to the stories. Record any unresolved
   Criticals for the gate.
8. **Phase 5 — Readiness.** Dispatch `Agent(avengers-dev:hulk)` to run
   `bmad-check-implementation-readiness` and return a PASS/FAIL verdict with
   reasons. **The gate reads the verdict Hulk returns**, not a file.
9. **HARD GATE** — Step 4. Do not enter Phase 6 without it.
10. **Phase 6 — Sprint Planning.** `Skill(bmad-sprint-planning)`.
11. **Phase 7 — Build.** For each story, dispatch `Agent(avengers-dev:thor)` to run
    `bmad-create-story`, then — **full track only** — `bmad-testarch-atdd` to write
    failing acceptance tests from the ACs, then `bmad-dev-story` (implement until
    the tests pass, commit), reporting back.
12. **Phase 8 — Review.** Dispatch `Agent(avengers-dev:captain)` to run
    `bmad-code-review`, then — **full track only** — `bmad-testarch-trace` to map
    every AC to a test (a trace FAIL loops the uncovered stories back to Phase 7),
    and `bmad-retrospective` at sprint end. On FAIL/CONDITIONAL, loop flagged
    stories back to Phase 7 (max 3 cycles, then escalate to the user). Phase 8 does
    **not** set `complete`; on a clean verdict it advances to Phase 9.
13. **Phase 9 — KB Refresh.** Step 5.

Update `current_phase` in the state file at each advance.

### 4. Design-Implementation Boundary — Hard Gate (Phase 5 → 6)

After Hulk reports the readiness verdict, IronMan presents it — plus any
unresolved Phase 4.5 Criticals — to the user in Vision's voice and **stops**.
Require an explicit choice:

> 🚧 Design-implementation boundary reached. The line must hold.
> **[1] Continue into implementation  [2] Exit** (artifacts saved, relay suspended)

No auto-advance, no batch-through.

- **Readiness PASS and no unresolved Criticals** — **[1]** sets
  `design_implementation_boundary_passed: true` and proceeds to Phase 6.
- **Readiness FAIL, or unresolved 4.5 Criticals** — **[1]** is accepted only if
  the user types `override` plus a reason. Record
  `gate_override: {reason, at}` in the state file, then pass the gate. A bare
  [1] is refused; restate the blockers.
- **[2]** sets `status: suspended` and stops.

### 5. Phase 9 — KB Refresh

1. Run `bmad-kb.py impact --base <kb_base_commit>`. Exit 0: JSON on stdout. Exit 2:
   no commits since base — set `status: complete` and stop. Exit 1 (bad sha or not
   a git repo): note it and set `complete`.
2. If `refresh_recommended` is false, set `status: complete`.
3. If true, show the user the `signals` and ask to confirm the refresh. On decline,
   set `complete`.
4. On confirm: if `changed_areas` has 3 or fewer entries, run
   `Skill(bmad-document-project)` in `deep_dive` once per area; otherwise run it in
   `full_rescan`.
5. Run `Skill(bmad-generate-project-context)` to update the context file.
6. Run `bmad-kb.py stamp`, then set `status: complete`.

### 6. Quick Track

1. Phase 0 as above (a `missing` KB is noted, not built — suggest `standard` if the
   change needs discovery).
2. Run `Skill(bmad-quick-dev)` in the main loop. Its own step-4 review replaces
   Captain's `bmad-code-review`.
3. Dispatch `Agent(avengers-dev:captain)` to review the resulting diff — a project
   rule: every code change gets Captain's review.
4. Phase 9 as in Step 5.

### 7. Phase Boundary Handling

At each main-loop phase completion, surface the boundary confirmation (§3.5) in
Vision's voice and wait for the user before advancing. Delegated phases report
through their Avenger; IronMan relays the result, then advances.

State file lives at `.avengers/relay-sequences/bmad-{name}.yaml` throughout.
