---
name: bmad
description: >
  Initiate or resume a BMAD sequence. Wraps the real BMAD-METHOD `bmad-*` skills
  and conducts them through the 8 phases in Vision's voice — interactive phases
  run in the main loop, non-interactive phases are delegated to the Avenger who
  owns them (BlackWidow, Hulk, Thor, Captain). IronMan holds the design-implementation
  hard gate.
allowed-tools: Skill, Agent, Bash, Read, Write
argument-hint: "[sequence-name] [resume]"
---

# BMAD — Conducting the Real BMAD-METHOD

This skill does **not** reimplement BMAD. It **wraps** the installed BMAD-METHOD
`bmad-*` skills and orchestrates them through the Avengers crew, narrating each
transition in **Vision's** voice. Vision is the conductor and the phase→skill+owner
map — not a subagent (a subagent runs blind and cannot elicit from the user, so
every interactive phase must run in this main loop).

**IronMan's job here:** run the sequence, speak in Vision's voice at each phase
boundary, dispatch the owning Avenger for delegated phases, and hold the
design-implementation hard gate (Phase 5 → 6).

## Ownership Map — phase → real skill → owner → mode

| Phase | Real skill(s) invoked | Owner | Mode |
| ----- | --------------------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` (brownfield) or `bmad-investigate` | `Agent(avengers-dev:blackwidow)` | autonomous subagent |
| 1b Brief | `bmad-product-brief` | IronMan (Vision voice), main loop | interactive |
| 2 PRD | `bmad-prd` | IronMan (Vision voice), main loop | interactive |
| 3 Architecture | `bmad-create-architecture` | IronMan (Vision voice), main loop | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | IronMan (Vision voice), main loop | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | `Agent(avengers-dev:hulk)` | autonomous subagent |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | IronMan (Vision voice), main loop | light / interactive |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | `Agent(avengers-dev:captain)` | autonomous subagent |

<!-- SEAM: Phases 1b–4 are interactive today because the real bmad-* skills elicit
     from the user, and a subagent cannot elicit. If those skills later gain a
     non-interactive / batch mode, these phases can be flipped to a fully-autonomous
     Vision subagent by moving their rows to "Agent(avengers-dev:vision)". Do not
     flip them while the wrapped skills still ask the user questions. -->

## Steps

> **Prompting (avoid "Invalid tool parameters"):** every user-facing question in
> this skill — the sequence name, the resume choice, and the Phase 5→6 [1]/[2]
> gate — is a **plain conversational question**. Ask it directly in the chat in
> Vision's voice and wait for the user's reply. Do **NOT** use a structured
> question/elicitation tool for these prompts; a plain text question has no schema
> to malform.

### 0. Preflight — BMAD-METHOD dependency check

This skill conducts the **real** BMAD-METHOD `bmad-*` skills, and each of them
expects a **project-level install** at `{project-root}/_bmad/` (config + scripts),
created by `npx bmad-method install`. Before anything else, verify it exists:

```bash
[ -d "_bmad" ] && echo "BMAD_OK" || echo "BMAD_MISSING"
```

- **`BMAD_MISSING`** → **STOP.** Do not parse args, create a state file, or begin a
  sequence. Announce, in Vision's voice, then exit:
  > 🔴 Vision — online. "BMAD-METHOD is not installed in this project. I conduct the
  > real framework — it needs its project config first. Run `npx bmad-method install`
  > in this directory, then re-run `/avengers-dev:bmad`."
- **`BMAD_OK`** → continue to Step 1.

### 1. Parse Arguments

- **No argument**: Prompt user for a sequence name. Kebab-case, descriptive.
  Example: "payment-gateway", "auth-modernization", "mobile-redesign".
- **`[sequence-name]`**: Initiate a new BMAD sequence with that name.
- **`[sequence-name] resume`** or **`resume [sequence-name]`**: Resume an existing sequence.
- **`resume`** (no name): List available sequences and prompt for selection.

### 2. Check for / Resume an Existing Sequence

```bash
ls .avengers/relay-sequences/bmad-*.yaml 2>/dev/null
```

If a sequence matching the name exists, ask (in Vision's voice):
"A BMAD sequence named '{name}' already exists. Resume it?"

On resume: read `.avengers/relay-sequences/bmad-{name}.yaml`, then announce
> 🔴 Vision — online. "Resuming BMAD '{name}' at Phase {N}: {phase-name}."
and re-enter the sequence at `current_phase` (respecting
`design_implementation_boundary_passed`).

On a new sequence: create the state file with `current_phase: 1`,
`status: active`, `design_implementation_boundary_passed: false`.
Schema reference: `${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md`.

### 3. Run the Phase Sequence

Open every phase transition with the Vision identity header + a matching
catchphrase (see `agents/vision.md`), then execute the phase per its **mode**:

- **Interactive phases (1b, 2, 3, 4, 6)** — invoke the real skill **in this main
  loop** with `Skill(bmad-X)` so it can elicit from the user directly. Announce
  in Vision's voice, run the skill, then confirm the phase boundary with the user
  before advancing (`§3.5` in relay-config).
- **Delegated phases (1a, 5, 7, 8)** — announce in Vision's voice, then dispatch
  the owning Avenger with `Agent(avengers-dev:owner)`, instructing that agent to
  run the named real skill autonomously and report back. Relay the agent's result
  in that agent's voice ("BlackWidow reports…", "Hulk says…", "Captain's verdict…").

Phase-by-phase:

1. **Phase 1a — Discovery.** Dispatch `Agent(avengers-dev:blackwidow)` to run
   `bmad-document-project` (brownfield: existing codebase → project context) or
   `bmad-investigate` (when tracing an area first). Greenfield with no code:
   skip 1a and note it in the state file.
2. **Phase 1b — Brief.** `Skill(bmad-product-brief)` in the main loop.
3. **Phase 2 — PRD.** `Skill(bmad-prd)` in the main loop.
4. **Phase 3 — Architecture.** `Skill(bmad-create-architecture)` in the main loop.
5. **Phase 4 — Epics & Stories.** `Skill(bmad-create-epics-and-stories)` in the main loop.
6. **Phase 5 — Readiness.** Dispatch `Agent(avengers-dev:hulk)` to run
   `bmad-check-implementation-readiness` autonomously and report the readiness verdict.
7. **HARD GATE** — see step 4 below. Do not enter Phase 6 without it.
8. **Phase 6 — Sprint Planning.** `Skill(bmad-sprint-planning)` in the main loop.
9. **Phase 7 — Build.** For each story in the sprint plan, dispatch
   `Agent(avengers-dev:thor)` to run `bmad-create-story` then `bmad-dev-story`
   for that story autonomously (implement + tests + commit), reporting back.
10. **Phase 8 — Review.** Dispatch `Agent(avengers-dev:captain)` to run
    `bmad-code-review` (and `bmad-retrospective` at sprint end) autonomously and
    report the verdict. On FAIL/CONDITIONAL, loop back to Phase 7 for the flagged
    stories (max 3 cycles, then escalate to the user).

Update `current_phase` in the state file at each advance.

### 4. Design-Implementation Boundary — Hard Gate (Phase 5 → 6)

After Hulk reports the readiness result, IronMan presents it to the user in
Vision's voice and **stops**. Require an explicit choice:

> 🚧 Design-implementation boundary reached. The line must hold.
> **[1] Continue into implementation  [2] Exit** (artifacts saved, relay suspended)

No auto-advance, no batch-through. On **[1]**: set
`design_implementation_boundary_passed: true` and proceed to Phase 6. On **[2]**:
set `status: suspended` and stop.

### 5. Phase Boundary Handling

At each interactive phase completion, surface the boundary confirmation
(`§3.5`) in Vision's voice and wait for the user before advancing. Delegated
phases report through their Avenger; IronMan relays the result, then advances.

State file lives at `.avengers/relay-sequences/bmad-{name}.yaml` throughout.
