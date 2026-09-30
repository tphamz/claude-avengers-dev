---
name: bmad
description: >
  Initiate or resume a BMAD sequence. Wraps the real BMAD-METHOD `bmad-*` skills
  and conducts them through the 8 phases in Vision's voice — every write-capable
  skill except the Phase 7 build runs in the main loop; the owning Avenger
  (BlackWidow, Hulk, Captain) then verifies the result read-only, and Thor builds.
  IronMan holds the design-implementation hard gate.
allowed-tools: Skill, Agent, Bash, Read, Write, Edit
argument-hint: "[sequence-name] [resume]"
---

# BMAD — Conducting the Real BMAD-METHOD

This skill does **not** reimplement BMAD. It **wraps** the installed BMAD-METHOD
`bmad-*` skills and orchestrates them through the Avengers crew, narrating each
transition in **Vision's** voice. Vision is the conductor and the phase→skill+owner
map — not a subagent (a subagent runs blind and cannot elicit from the user, so
every interactive phase must run in this main loop).

**IronMan's job here:** run the sequence, speak in Vision's voice at each phase
boundary, dispatch the owning Avenger to verify (or, in Phase 7, build), and hold
the design-implementation hard gate (Phase 5 → 6).

**Why the main loop:** the wrapped skills write artifacts step by step, halt for
user input, and (`bmad-code-review`) spawn their own subagents. BlackWidow, Hulk
and Captain are read-only subagents with no Write, Edit or Agent tools, so they
cannot run these skills. They verify instead. The main loop may read broadly and
write BMAD artifacts while running a wrapped skill, but never modifies source
code — code changes always go to Thor.

## Ownership Map — phase → real skill → owner → mode

| Phase | Real skill(s) invoked | Owner | Mode |
| ----- | --------------------- | ----- | ---- |
| 1a Discovery | `bmad-document-project` (brownfield) or `bmad-investigate` | main loop; `Agent(avengers-dev:blackwidow)` verifies | interactive + read-only verify |
| 1b Brief | `bmad-product-brief` | IronMan (Vision voice), main loop | interactive |
| 2 PRD | `bmad-prd` | IronMan (Vision voice), main loop | interactive |
| 3 Architecture | `bmad-create-architecture` | IronMan (Vision voice), main loop | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | IronMan (Vision voice), main loop | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | interactive + read-only verify |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | IronMan (Vision voice), main loop | light / interactive |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | `Agent(avengers-dev:thor)` per story | autonomous subagent |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | interactive + read-only verify |

<!-- SEAM: Every wrapped skill above except Phase 7 runs in the main loop because
     it elicits from the user and writes artifacts, and the read-only owners
     cannot do either. If those skills later gain a batch mode, a phase could move
     to a write-capable subagent. Do not move it to a read-only agent, and do not
     move it while the skill still asks the user questions. -->

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

- **Main-loop phases (1b, 2, 3, 4, 6)** — invoke the real skill **in this main
  loop** with `Skill(bmad-X)` so it can elicit from the user directly. Announce
  in Vision's voice, run the skill, then confirm the phase boundary with the user
  before advancing (`§3.5` in relay-config).
- **Main loop + verify (1a, 5, 8)** — run the real skill in this main loop, then
  resolve the concrete artifact paths from `_bmad/bmm/config.yaml` (relay-config
  `§2.8`) and dispatch the owning Avenger read-only to verify them. Pass real
  file paths, never globs or unresolved `{placeholders}`. Relay the result in that
  agent's voice ("BlackWidow reports…", "Hulk says…", "Captain's verdict…").
- **Build (7)** — dispatch `Agent(avengers-dev:thor)` per story (unchanged).

Phase-by-phase:

1. **Phase 1a — Discovery.** Run `Skill(bmad-document-project)` (brownfield:
   existing codebase → project docs under `{project_knowledge}`, default `docs/`)
   or `Skill(bmad-investigate)` (when tracing an area first → case file at
   `{implementation_artifacts}/investigations/{slug}-investigation.md`) in the main
   loop. Then dispatch `Agent(avengers-dev:blackwidow)` with the resolved output
   paths to verify them against the codebase. Greenfield with no code: skip 1a and
   note it in the state file.
2. **Phase 1b — Brief.** `Skill(bmad-product-brief)` in the main loop.
3. **Phase 2 — PRD.** `Skill(bmad-prd)` in the main loop.
4. **Phase 3 — Architecture.** `Skill(bmad-create-architecture)` in the main loop.
5. **Phase 4 — Epics & Stories.** `Skill(bmad-create-epics-and-stories)` in the main loop.
6. **Phase 5 — Readiness.** Run `Skill(bmad-check-implementation-readiness)` in
   the main loop. It writes
   `{planning_artifacts}/implementation-readiness-report-{date}.md` with a status
   of READY / NEEDS WORK / NOT READY. Then dispatch `Agent(avengers-dev:hulk)`
   with the path of the newest report file (not a glob) and the planning artifacts
   it assessed, for an independent verdict: READY / READY-WITH-CONCERNS / NOT-READY.
7. **HARD GATE** — see step 4 below. Do not enter Phase 6 without it.
8. **Phase 6 — Sprint Planning.** `Skill(bmad-sprint-planning)` in the main loop.
9. **Phase 7 — Build.** For each story in the sprint plan, dispatch
   `Agent(avengers-dev:thor)` to run `bmad-create-story` then `bmad-dev-story`
   for that story autonomously (implement + tests + commit), reporting back.
10. **Phase 8 — Review.** Per story, in this order (full detail in
    `references/bmad/phase-8-review.md`):
    1. **Code review (main loop).** Run `Skill(bmad-code-review)` with the story
       file set as the spec. Resolve every `decision-needed` finding with the user
       at its step 4. At the patch menu, tell the user to pick **"Leave as action
       items"**, then **"Done"** at the next-steps menu. The main loop never
       applies patches. If the user picks "Apply every patch" anyway, stop and
       hand the patch list to Thor instead of applying it. Because the story is
       passed as the spec file, code-review never sets `{story_key}`, so its own
       `sprint-status.yaml` sync is skipped — close-out (step 7) does it instead.
    2. **Reconcile Review Findings (main loop).** In the story's
       `### Review Findings`, make sure every decision the user converted to a
       patch is recorded as an unchecked `- [ ] [Review][Patch] ...` bullet, and
       mark each resolved `[Review][Decision]` bullet checked (`[x]`) or strike it
       through. Unchecked Decision bullets make `bmad-dev-story` step 9 HALT.
    3. **Fix (Thor).** If unchecked `[Review][Patch]` items exist after
       reconciliation, dispatch `Agent(avengers-dev:thor)` with the explicit story
       file path (dev-story auto-discovery only picks `ready-for-dev` stories) and
       the `[Review][Patch]` items named one by one (the skill's review-continuation
       check looks for the older "Senior Developer Review (AI)" section). Thor runs
       `bmad-dev-story` on that path, resolves the items, runs tests and commits.
    4. **Review (Captain).** Read `baseline_commit` from the story file's
       frontmatter (written by dev-story) and dispatch `Agent(avengers-dev:captain)`
       with the story file path and the concrete range
       `<baseline_commit>..HEAD`. Verdict: PASS | CONDITIONAL PASS | FAIL.
    5. **Verify (BlackWidow).** Dispatch `Agent(avengers-dev:blackwidow)` to verify
       Captain's findings.
    6. **Cycle.** A FAIL, or a CONDITIONAL PASS (Warnings), goes back to Thor with
       the verified findings → Captain → BlackWidow. The limit is 3 cycles. After
       the third, present the verdict to the user, who either accepts the
       CONDITIONAL PASS or exits (`status: suspended`). A FAIL cannot be accepted.
    7. **Close-out (main loop).** After a PASS (or a user-accepted CONDITIONAL
       PASS at the cycle limit) and BlackWidow's verification, set the story
       file's `Status: done`, and in `{implementation_artifacts}/sprint-status.yaml`
       set `development_status[<story_key>]: done` (the key is the story file's
       basename, e.g. `1-2-user-auth`) and `last_updated` to today, preserving all
       comments and structure. This is a BMAD artifact write, allowed under the
       wrapped-skill exception.
    8. **Retrospective (main loop, at epic completion).** Epic N is complete when
       every story key for epic N (keys starting `N-`, excluding `epic-N` and
       `epic-N-retrospective`) is `done` in `sprint-status.yaml`. Only then run
       `Skill(bmad-retrospective)`. It writes
       `{implementation_artifacts}/epic-{N}-retro-{date}.md` and updates
       `sprint-status.yaml`. Relay its output; no Captain verification.

Update `current_phase` in the state file at each advance.

### 4. Design-Implementation Boundary — Hard Gate (Phase 5 → 6)

After Hulk reports, IronMan presents **both** results to the user in Vision's
voice — the skill report's status and Hulk's verdict — and **stops**. If either is
NOT READY / NOT-READY, recommend [2]. If either is NEEDS WORK /
READY-WITH-CONCERNS, flag it explicitly and list the cited gaps. In every case the
user decides. Require an explicit choice:

> 🚧 Design-implementation boundary reached. The line must hold.
> **[1] Continue into implementation  [2] Exit** (artifacts saved, relay suspended)

No auto-advance, no batch-through. On **[1]**: set
`design_implementation_boundary_passed: true` and proceed to Phase 6. On **[2]**:
set `status: suspended` and stop.

### 5. Phase Boundary Handling

At each main-loop phase completion, surface the boundary confirmation
(`§3.5`) in Vision's voice and wait for the user before advancing. For phases
with a verifying Avenger (1a, 5, 8) and the Phase 7 build, IronMan relays the
Avenger's result, then advances.

State file lives at `.avengers/relay-sequences/bmad-{name}.yaml` throughout.
