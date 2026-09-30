---
name: bmad
description: >
  Initiate or resume a BMAD sequence as a spec-driven relay over the real
  BMAD-METHOD `bmad-*` skills, in Vision's voice. Three tracks — quick, standard,
  full — with a knowledge-base (KB) lifecycle (build when missing, refresh when
  stale or after impactful changes), spec hardening before the gate, and
  ATDD + requirement-to-test trace on the full track. Every wrapped skill except
  the code-writing ones (`bmad-dev-story`, and `bmad-testarch-atdd` on the full
  track) runs in the main loop (Phase 7's `bmad-create-story` included); the
  owning Avenger (BlackWidow, Captain, Hulk) then verifies the result read-only,
  and Thor builds, his HALTs relayed to the user. IronMan holds the
  design-implementation hard gate.
allowed-tools: Skill, Agent, Bash, Read, Write, Edit, WebSearch, WebFetch
argument-hint: "[sequence-name] [quick|standard|full|resume]"
---

# BMAD — Conducting the Real BMAD-METHOD

This skill does **not** reimplement BMAD. It **wraps** the installed BMAD-METHOD
`bmad-*` skills and orchestrates them through the Avengers crew, narrating each
transition in **Vision's** voice. Vision is the conductor and the phase→skill+owner
map — not a subagent (a subagent runs blind and cannot elicit from the user, so
every interactive skill must run in this main loop).

**IronMan's job here:** run the sequence, speak in Vision's voice at each phase
boundary, dispatch the owning Avenger to verify (or, in Phase 7, dispatch Thor
to run `bmad-dev-story` and relay his Blocked reports to the user), and hold the
design-implementation hard gate (Phase 5 → 6).

**Why the main loop:** the wrapped skills write artifacts step by step, halt for
user input, and (`bmad-code-review`) spawn their own subagents. BlackWidow, Hulk
and Captain are read-only subagents with no Write, Edit or Agent tools, so they
cannot run these skills. They verify instead. `bmad-dev-story` and (full track)
`bmad-testarch-atdd` change source code, so Thor runs them, and each stop that
needs a human comes back as a Blocked report. The main loop may read broadly and
write BMAD artifacts and relay bookkeeping (state file, `bmad-kb.py stamp`
outputs, `workstation.py set` repair; full list in relay-config `§3.12`), but
never modifies source code — code changes always go to Thor. **Quick-track
exception:** on the quick track, `bmad-quick-dev` runs in the main loop and
implements the code; it is the one sanctioned case where the main loop writes
source code (Captain's fixes still go to Thor by default, Step 6).

The KB helper script is `${CLAUDE_PLUGIN_ROOT}/skills/bmad/scripts/bmad-kb.py`
(referred to below as **bmad-kb.py**). The md workstation script is
`${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py`
(**workstation.py**). Every subcommand of both accepts `--project-dir` (default:
current directory) and prints `--help`.

## Ownership Map — phase → real skill → owner → tracks

| Phase | Real skill(s) invoked | Owner | Tracks |
| ----- | --------------------- | ----- | ------ |
| 0 KB check | `bmad-kb.py status` | main loop | all |
| 1a Discovery (KB `missing`, or `stale` and user accepts) | `bmad-document-project` + `bmad-generate-project-context`, then `bmad-kb.py stamp` | main loop (Vision voice); `Agent(avengers-dev:blackwidow)` verifies | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` (create); optional `bmad-prd` validate / `bmad-advanced-elicitation` | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | main loop; `Agent(avengers-dev:captain)` (`adversarial` lens) verifies and assigns severity; fixes in main loop | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | standard, full |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full only) → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-testarch-atdd` (full only) and `bmad-dev-story` per story (HALTs relayed) | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full only) + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → `bmad-document-project` + `bmad-generate-project-context` → `bmad-kb.py stamp` | main loop (Vision voice) | all |
| Quick track | `bmad-quick-dev`, then Captain reviews the diff | main loop, then `Agent(avengers-dev:captain)` | quick |

<!-- SEAM: Every wrapped skill above except the code-writing ones runs in the main
     loop because it elicits from the user and writes artifacts, and the read-only
     owners cannot do either. bmad-dev-story (and bmad-testarch-atdd) run in Thor
     because they change source code; their HALTs return as a Blocked report that
     the main loop relays. If those skills later gain a batch mode, a phase could
     move to a write-capable subagent. Do not move it to a read-only agent, and do
     not move it while the skill still asks the user questions. -->

## Tracks

| Track | Phases | Use when |
| ----- | ------ | -------- |
| `quick` | 0 → quick-dev → Captain diff review → 9 | small, well-understood change; no PRD/architecture needed |
| `standard` | 0 → 1a (conditional) → 1b → 2 → 3 → 4 → 4.5 → 5 → gate → 6 → 7 → 8 → 9 | default for features and initiatives |
| `full` | as standard, plus ATDD in 7 and trace in 8 | acceptance tests must be written first and traced to ACs; needs the TEA module |

## Steps

> **Prompting (avoid "Invalid tool parameters"):** every user-facing question in
> this skill — the sequence name, the track, the resume choice, the md workstation
> location, the stale-KB refresh offer, the md commit offers, the Phase 5→6 [1]/[2]
> gate, each Blocked relay (answer or suspend), and the Phase 9 refresh
> confirmation — is a **plain conversational question**. Ask it directly in the
> chat in Vision's voice and wait for the user's reply. Do **NOT** use a structured
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

**md workstation check (every run).** After preflight passes, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py resolve
```

Run it every time — a symlink can dangle and a BMAD reinstall can undo a re-point.
Exit 0: JSON with `state` and `symlink`. Exit 1: report the error and continue
in-repo.

- `ok` with every `symlinks` value `ok` — nothing to ask.
- `ok` with any other `symlinks` value — repair silently with
  `workstation.py set --path <path>` (it keeps any link `/sdd` added).
- `in_repo` — the user keeps markdown in the repo; continue.
- `guess`, `missing`, or `broken` — run the interactive flow of
  `/avengers-dev:avengers-workstation` (Steps 1–4 of that skill: confirm or ask for
  the md root, `set` or `migrate`, grant access). The user may answer "in-repo".

Then run `workstation.py check-config` (skip if no workstation). Exit 0: nothing
to do. Exit 1 (`_bmad/` missing, or `output_folder` outside the project): relay
stderr once, skip the re-point offers, and continue. Exit 2: for each `outside` entry with `declined: false`, offer the opt-in
re-point exactly as in Step 5 of `/avengers-dev:avengers-workstation` (warning that
it edits the team's committed config; decline is recorded and not asked again).
Declined keys keep that artifact in the repo — mention it once.

Record the resolved path as `md_workstation` in the state file (Step 2), or `null`
when there is none.

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

On resume: read `.avengers/relay-sequences/bmad-{name}.yaml`. If it is
a **legacy state file** — one with no `track` key (written before tracks and Phases 0/4.5/9 existed), apply the **resume defaults** (relay-config §3.2):

- treat `track` as `standard`
- if it is at `8` or `complete`, finish as before — it is **not** routed into
  Phase 9
- otherwise it continues through Phase 9 at the end; with no `kb_base_commit`,
  Phase 9 uses the `stamped_commit` reported by `bmad-kb.py status`, or is
  skipped with a note if there is none

State files that have a `track` key follow the normal flow, including Phase 9.

then announce
> 🔴 Vision — online. "Resuming BMAD '{name}' ({track}) at Phase {N}: {phase-name}."
and re-enter at `current_phase` (respecting `design_implementation_boundary_passed`).

On re-entering Phase 7 or 8, follow
relay-config `§3.2`. Resume decisions come from each story's `phase7_step` /
`phase8_step` marker, never from `loop_state.completed` (every story is in it
once Phase 7 ends). Marker inference (relay-config State Schema) runs first,
when the state file is read, and fills in missing markers for every
`development_status` key (epic keys `epic-N` and `epic-N-retrospective` are
excluded): no `phase7_step` → `dispatched` if it has
`loop_state.stories[<key>].baseline_commit` (not just a frontmatter one), no
`phase7_end_sha`, is not in `completed` and is not `done` (tested first; a
`done` story matching the rest is never re-dispatched — ask the user which
Phase 7 step it reached), else `recorded` if
the key is in `completed`, at `review` or `done`, or has a `phase7_end_sha`
(Phase 8 then uses the `§2.9` resume fallback if that SHA is missing), else
`pending`; no `phase8_step` → `closed` if `done`, else `pending` only if no fix
ranges and `review_cycles` 0; otherwise ask the user. In order:

1. **Blocked replay.** If any `loop_state.stories` entry has a `blocked` entry,
   first replay its stored HALT point, question, options and work state to the
   user and ask: answer, or keep it suspended. Do this before any dispatch. Keep
   suspended → leave `status: suspended` and stop. Answer → continue at Phase 7
   step 4's answer path (the `[Gate]` subtask and the status reset where they
   apply), re-dispatching Thor with the answer, the stored work state and the
   stored resume instruction; the chain start is the recorded `baseline_commit`
   (Phase 7) or `chain_start_sha` (Phase 8). When that chain reports done: a
   Phase 7 chain continues at Phase 7 step 5; a Phase 8 fix chain records its
   fix range (`§2.9` checks, `chain_start_sha` → null, `phase8_step: captain`)
   and continues at Phase 8 step 4 (Captain).
2. **Orphaned Phase 8 fix chain** (`chain_start_sha` set, `blocked` null,
   `phase8_step: fixing`). Ask the user: re-dispatch Thor to finish the fix, or
   treat the chain as done. Done → run the `§2.9` checks on
   `<chain_start_sha>..<HEAD now>`, record that range, and continue at Phase 8
   step 4.
3. **The Phase 7 loop** (step 11 below) skips a story only at
   `phase7_step: recorded`. `done_reported`, or `dispatched` with no `blocked`
   and the story at `review` → take `post_sha` from HEAD now, run the `§2.9`
   checks, do Phase 7 step 5, and tell the user the range was recovered.
   `dispatched` with no `blocked` and not at `review` → re-dispatch at step 2 as
   an agent-failure retry. `pending` → step 1.
4. **The Phase 8 loop** (step 12 below) skips a story only at
   `phase8_step: closed`. `pending` → step 1; `code_review_done` or `fixing` →
   step 2 only if not already done, then step 3 if unchecked `[Review][Patch]`
   or `[Gate]` items remain, else step 4 (full track, at `code_review_done`: a
   recorded `trace_report` whose untested ACs have no matching `Cover AC <n>`
   bullet gets those bullets re-derived from the report first; the trace never
   re-runs); `captain` → step 4; `verify` → step 5
   with the stored `captain_findings`. Never re-run code review past `pending`,
   never set a `closed` story back to `in-progress`, and carry `review_cycles`
   over unchanged. Then run any retrospective still owed.

On a new sequence: create the state file with `current_phase: 0`, `track`,
`status: active`, `design_implementation_boundary_passed: false`,
`gate_override: null`, `md_workstation: <path>|null`. On resume, refresh
`md_workstation` from the Step 0 check. Schema reference:
`${CLAUDE_PLUGIN_ROOT}/references/bmad/relay-config.md`.

### 3. Run the Phase Sequence

Open every phase transition with the Vision identity header + a matching
catchphrase (see `agents/vision.md`), then execute the phase per its owner:

- **Main-loop phases (0, 1b, 2, 3, 4, 6, 9, quick-dev)** — invoke the real
  skill **in this main loop** with `Skill(bmad-X)` so it can elicit from the user
  directly. Announce in Vision's voice, run the skill, then confirm the phase
  boundary with the user before advancing (`§3.5` in relay-config).
- **Main loop + verify (1a, 4.5, 5, 8)** — run the real skill in this main loop,
  then resolve the concrete artifact paths from `_bmad/bmm/config.yaml`
  (relay-config `§2.8`) and dispatch the owning Avenger read-only to verify them.
  Pass real file paths, never globs or unresolved `{placeholders}`. Relay the
  result in that agent's voice ("BlackWidow reports…", "Captain's verdict…",
  "Hulk says…").
- **Build (7)** — run `Skill(bmad-create-story)` in this main loop, then
  dispatch `Agent(avengers-dev:thor)` to run `bmad-testarch-atdd` (full track
  only) and `bmad-dev-story`, per story; relay each Blocked report to the user
  (relay-config `§3.8`).

Phase-by-phase (standard and full tracks; quick track is Step 6):

1. **Phase 0 — KB check.** Run `bmad-kb.py status` (exit 0: JSON on stdout; exit 1:
   `_bmad/` missing — stop as in Step 0). Record `state` as `kb_status_at_start`
   and the `head` value as `kb_base_commit`.
   - `missing` → run Phase 1a.
   - `stale` → show the `signals` and offer a refresh; run 1a only if the user accepts.
   - `unstamped` → the KB exists but its age is unknown; offer a refresh as for
     `stale`. If declined, run `bmad-kb.py stamp` (git repos only) so later runs
     can measure drift, and skip 1a.
   - `fresh` or `unknown` → skip 1a (note `unknown` = not a git repo).
   - A `signals` entry of type `unknown_stamp` means the stamped commit is no
     longer in history (e.g. rebased away); treat it as `stale`.

   **Not a git repo** (`head` is null): never run `bmad-kb.py stamp` — it would
   exit 1. Freshness cannot be tracked; note it in the state file.
2. **Phase 1a — Discovery (main loop).** `Skill(bmad-document-project)` —
   `initial_scan` when missing, `full_rescan` when refreshing a stale KB — then
   `Skill(bmad-generate-project-context)`, then — git repos only — `bmad-kb.py
   stamp` (exit 0 stamped; exit 2 already stamped at HEAD, fine; exit 1 error,
   report it). Both skills halt for user input and write as they go, so neither
   runs in a read-only subagent. Then dispatch `Agent(avengers-dev:blackwidow)`
   with the resolved output paths (relay-config `§2.8`) to verify them against
   the codebase. Greenfield with no code: skip 1a and note it in the state file.
   Then offer an **md commit** (Step 8).
3. **Phase 1b — Brief.** `Skill(bmad-product-brief)`.
4. **Phase 2 — PRD.** `Skill(bmad-prd)` in create mode (it runs its own reviewer
   gate). Then **offer**, as a plain question, an optional `bmad-prd` validate pass
   and/or `Skill(bmad-advanced-elicitation)`. Skip both if the user declines.
5. **Phase 3 — Architecture.** `Skill(bmad-create-architecture)`.
6. **Phase 4 — Epics & Stories.** `Skill(bmad-create-epics-and-stories)`.
7. **Phase 4.5 — Spec Hardening.** Run `Skill(bmad-review-adversarial-general)`
   and `Skill(bmad-review-edge-case-hunter)` in the main loop over the stories and
   acceptance criteria (ACs), checking every AC is testable. Then dispatch
   `Agent(avengers-dev:captain)` with the `adversarial` lens, the resolved story
   paths and both skills' findings, to verify them read-only (no test gate:
   this is a pre-implementation spec review, `agents/captain.md` Hardening
   Verification (/bmad 4.5, /sdd H)). **Captain assigns
   the `[CRITICAL]`/`[WARNING]`/`[SUGGESTION]` tags** — the wrapped skills emit no
   severity. Captain reports only; back in the main loop, walk the findings with
   the user and apply the agreed fixes to the stories. Record any unresolved
   Criticals for the gate.
8. **Phase 5 — Readiness.** Run `Skill(bmad-check-implementation-readiness)` in
   the main loop. It writes
   `{planning_artifacts}/implementation-readiness-report-{date}.md` with a status
   of READY / NEEDS WORK / NOT READY. Then dispatch `Agent(avengers-dev:hulk)`
   with the path of the newest report file (not a glob) and the planning artifacts
   it assessed, for an independent verdict: READY / READY-WITH-CONCERNS / NOT-READY.
9. **HARD GATE** — Step 4. Do not enter Phase 6 without it.
10. **Phase 6 — Sprint Planning.** `Skill(bmad-sprint-planning)` in the main loop.
11. **Phase 7 — Build.** For each story, in `development_status` order (full
   detail in relay-config `§3.8`). Skip a story only when its `phase7_step` is
   `recorded` (`pending` → `dispatched` → `done_reported` → `recorded`, each
   saved immediately); other values re-enter as the resume rules above say.
   Marker inference has already run, so a story at `review` or `done` with no
   `loop_state.stories` entry (e.g. from an earlier sequence) is skipped.
   1. **Create (main loop).** Skip if the story is already past `backlog`.
      Otherwise check the epic's `sprint-status.yaml` entry: `backlog` or
      `contexted` → set it to `in-progress`; `in-progress` → no change; `done` →
      stop and ask the user; anything else → stop. Run `Skill(bmad-create-story)` with the full
      `development_status` key (e.g. `1-2-user-auth`). The user answers its
      menus; this main loop does its web research. Afterwards, check that the
      story file and its `sprint-status.yaml` entry are both `ready-for-dev`;
      stop if not.
   2. **Record `pre_sha`** (`git rev-parse HEAD`; the empty-tree hash if it
      fails), resolve the story file path, and set `loop_state.in_progress` to
      the story (at every dispatch). If the story has no `baseline_commit` in
      `loop_state`, write this `pre_sha` as `baseline_commit`; never overwrite
      an existing one. Set `phase7_step: dispatched` and save the state file
      before dispatching.
   3. **Build (Thor).** Dispatch `Agent(avengers-dev:thor)` to run
      `bmad-dev-story` on the explicit story file path (implement + tests +
      commit). **Full track only:** in the same dispatch, before dev-story, he
      runs `bmad-testarch-atdd` to write failing acceptance tests from the
      story's ACs (skipped on a re-dispatch once those tests exist), so dev-story
      implements until they pass. Instruct him: at any HALT or ask point in
      `bmad-testarch-atdd` or `bmad-dev-story`, do not guess or work around it
      — stop without committing and return a Blocked report; dev-story's
      step-10 completion prompts are not stops.
   4. **Blocked.** Record `blocked` in `loop_state.stories[<story_key>]`
      (HALT point, question, options, work state, resume instruction,
      `dispatched_at_sha`), show the user the HALT point, question, options and
      work state, and ask: answer or suspend. On an answer: for a step-9
      regression or definition-of-done HALT, append an unchecked
      `- [ ] [Gate] Fix <failure>: <user answer>` subtask to
      `## Tasks / Subtasks` (no subtask for "any task is incomplete", whose
      unchecked task already resumes dev-story, or "File List is incomplete",
      which Thor fixes directly); if dev-story already set `review`, reset the
      story file and `sprint-status.yaml` entry to `in-progress`. Clear
      `blocked` (the chain start stays in `baseline_commit`), record a new
      `pre_sha`, and re-dispatch Thor with the answer, the previous Work state
      and the Resume instruction. No cap; real agent failures retry up to 2
      times, then escalate.
   5. **Done.** On the done report set `phase7_step: done_reported` and save,
      before any check. Record `post_sha` (never the SHA from Thor's report) and run the
      `§2.9` checks on `<baseline_commit>..<post_sha>`. The uncommitted-files
      check flags only paths in the story's File List or Thor's reported files;
      if it flags, Thor's commit dispatch joins the same chain, then take
      `post_sha` again, rerun the checks and record it. Cross-check
      `baseline_commit` against the story frontmatter (a frontmatter `NO_VCS` in
      a git repository is ignored). Write `phase7_end_sha` (the final
      `post_sha`, never overwriting one) to `loop_state.stories[<story_key>]`,
      add the key to `completed`, set `in_progress` to null, update
      `remaining`, and set `phase7_step: recorded`, in one state write.
12. **Phase 8 — Review.** On entry, write `phase8_start_sha` (`git rev-parse
    HEAD`) to `loop_state` once, and set `phase8_step: pending` only on stories
    still unmarked after marker inference (a `done` story was inferred `closed`
    and is never set to `pending`). Then per story, in this order (full detail in
    `references/bmad/phase-8-review.md`; each `phase8_step` change is saved
    immediately, relay-config `§3.9`). Skip a story at `phase8_step: closed`. The story's review ranges are
    `<baseline_commit>..<phase7_end_sha>` plus each range in
    `phase8_fix_ranges`, from `loop_state.stories[<story_key>]`; never `..HEAD`,
    which includes later stories. If a story has no `phase7_end_sha`, use the
    `§2.9` resume fallback. An empty-tree left side follows `§2.9` **Unborn
    HEAD**.
    1. **Code review (main loop).** Run `Skill(bmad-code-review)` with the story
       file set as the spec and the explicit range
       `<baseline_commit>..<phase7_end_sha>`. Resolve every `decision-needed`
       finding with the user at its step 4. At the patch menu, tell the user to
       pick **"Leave as action items"**, then **"Done"** at the next-steps menu. The main loop never
       applies patches. If the user picks "Apply every patch" anyway, stop and
       hand the patch list to Thor instead of applying it. Because the story is
       passed as the spec file, code-review never sets `{story_key}`, so its own
       `sprint-status.yaml` sync is skipped — close-out (step 7) does it instead.
       **Full track only:** after "Done", run `Skill(bmad-testarch-trace)` for
       the story in the main loop to map every AC to a test. Right after it,
       write each AC it reports untested into the story's `### Review Findings`
       (inside `## Tasks / Subtasks`) as an unchecked
       `- [ ] [Review][Patch] Cover AC <n>: ...` bullet (skip any already
       present), so it loops back through Thor. Then, in one state write, record
       `trace_report: <report path>` in `loop_state.stories[<story_key>]` and
       set `code_review_done`.
       Runs only at `phase8_step: pending`; on the standard track, set
       `code_review_done` after "Done".
    2. **Reconcile Review Findings (main loop).** In the story's
       `### Review Findings`, make sure every decision the user converted to a
       patch is recorded as an unchecked `- [ ] [Review][Patch] ...` bullet, and
       mark each resolved `[Review][Decision]` bullet checked (`[x]`); striking
       it through is optional and does not replace `[x]`. Unchecked Decision
       bullets make `bmad-dev-story` step 9 HALT. Make sure `### Review Findings`
       sits inside `## Tasks / Subtasks`, where dev-story looks for tasks, and
       merge any duplicate `### Review Findings` section (a re-run code review
       appends a second one) into it, keeping each bullet once. Trace output is
       not converted here; step 1 already wrote the `Cover AC` bullets, so only
       dedupe against them. On a resume at
       `code_review_done` with unchecked `[Review][Decision]` bullets, the
       code-review conversation is lost: ask the user to decide each directly.
       Set the story's `sprint-status.yaml` entry to `in-progress`. No unchecked
       `[Review][Patch]` or `[Gate]` items → set `phase8_step: captain`, go to
       step 4.
    3. **Fix (Thor).** If unchecked `[Review][Patch]` items exist after
       reconciliation, dispatch `Agent(avengers-dev:thor)` with the explicit story
       file path (dev-story auto-discovery only picks `ready-for-dev` stories) and
       the `[Review][Patch]` items named one by one (the skill's review-continuation
       check looks for the older "Senior Developer Review (AI)" section). Thor runs
       `bmad-dev-story` on that path, resolves the items, runs tests and commits.
       The dispatch carries the Phase 7 stop instruction; a Blocked report is
       handled as in Phase 7 step 4 (relay, `[Gate]` subtask for a regression
       or definition-of-done HALT, `in-progress` reset, re-dispatch with the
       answer, Work state and Resume instruction), and Blocked re-dispatches do
       not count toward `review_cycles`. Record `pre_sha` before every dispatch
       and `post_sha` after every report. Before the chain's first dispatch,
       write its `pre_sha` as `chain_start_sha` (keep it if already set) and
       set `phase8_step: fixing`, in one write; on the done report run the
       `§2.9` checks, append the fix range `<chain_start_sha>..<done post_sha>`
       to `phase8_fix_ranges`, set `chain_start_sha` to null and
       `phase8_step: captain` in one write, and go to step 4.
    4. **Review (Captain).** Dispatch `Agent(avengers-dev:captain)` with the
       story file path, the concrete range `<baseline_commit>..<phase7_end_sha>`
       and each range in `phase8_fix_ranges`, each reviewed with
       `git diff <range>`. If `baseline_commit` is `NO_VCS`, pass the story's
       File List instead; Captain reviews those files as they stand now.
       Verdict: PASS | CONDITIONAL PASS | FAIL. Increment `review_cycles`,
       store the verdict and findings in `captain_findings`, set
       `phase8_step: verify`, and save, in one write (relay-config `§2.10`).
    5. **Verify (BlackWidow).** Dispatch `Agent(avengers-dev:blackwidow)` with
       the story file path, the same ranges (or File List) Captain received, and
       Captain's findings, to verify them for false positives.
    6. **Cycle.** A FAIL, or a CONDITIONAL PASS (Warnings), goes back to Thor.
       First append the verified Captain and BlackWidow findings to the story's
       `### Review Findings` as unchecked `- [ ] [Review][Patch] ...` bullets
       (dev-story implements only story tasks; skip findings already present)
       and set the `sprint-status.yaml` entry to `in-progress`; then set
       `phase8_step: fixing` and Thor runs as in step 3 → Captain →
       BlackWidow. The limit is 3 cycles, counted in `review_cycles` (one cycle
       per Captain verdict). After the third, present the verdict to the user, who either accepts the
       CONDITIONAL PASS or exits (`status: suspended`). A FAIL cannot be accepted.
    7. **Close-out (main loop).** After a PASS (or a user-accepted CONDITIONAL
       PASS at the cycle limit) and BlackWidow's verification, set the story
       file's `Status: done`, and in `{implementation_artifacts}/sprint-status.yaml`
       set `development_status[<story_key>]: done` (the key is the story file
       name without `.md`, e.g. `1-2-user-auth`) and `last_updated` to today,
       preserving all comments and structure. This is a BMAD artifact write, allowed under the
       wrapped-skill exception. Then set `phase8_step: closed` and save.
    8. **Retrospective (main loop, at epic completion).** Epic N is complete when
       every story key for epic N (keys starting `N-`, excluding `epic-N` and
       `epic-N-retrospective`) is `done` in `sprint-status.yaml`. Only then run
       `Skill(bmad-retrospective)` with epic N passed explicitly. It writes
       `{implementation_artifacts}/epic-{N}-retro-{date}.md` and updates
       `sprint-status.yaml`. Relay its output; no Captain verification.

    Phase 8 does **not** set `complete`; once every epic is closed out and its
    retrospective has run, it advances to Phase 9.
13. **Phase 9 — KB Refresh.** Step 5.

Update `current_phase` in the state file at each advance.

### 4. Design-Implementation Boundary — Hard Gate (Phase 5 → 6)

After Hulk reports, offer an **md commit** (Step 8) for the design artifacts.
Then IronMan presents **both** results to the user in Vision's voice — the skill
report's status and Hulk's verdict — plus any unresolved Phase 4.5 Criticals, and
**stops**. If either is NOT READY / NOT-READY, recommend [2]. If either is NEEDS
WORK / READY-WITH-CONCERNS, flag it explicitly and list the cited gaps. In every
case the user decides. Require an explicit choice:

> 🚧 Design-implementation boundary reached. The line must hold.
> **[1] Continue into implementation  [2] Exit** (artifacts saved, relay suspended)

No auto-advance, no batch-through.

- **Neither result NOT READY / NOT-READY, and no unresolved Criticals** — **[1]** sets
  `design_implementation_boundary_passed: true` and proceeds to Phase 6.
- **Either result NOT READY / NOT-READY, or unresolved 4.5 Criticals** — **[1]** is accepted only if
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

Whichever way Phase 9 ends (steps 1–6, on every track), offer an **md commit**
(Step 8) before announcing completion.

### 6. Quick Track

1. Phase 0 as above (a `missing` KB is noted, not built — suggest `standard` if the
   change needs discovery).
2. Run `Skill(bmad-quick-dev)` in the main loop; it implements the code. This is
   the one sanctioned case where the main loop writes source code (relay-config
   `§3.12`). Its own step-4 review replaces Captain's `bmad-code-review`.
3. Dispatch `Agent(avengers-dev:captain)` to review the resulting diff — a project
   rule: every code change gets Captain's review.
4. **Fix loop.** On FAIL, or CONDITIONAL PASS with any `[CRITICAL]`, fix the
   flagged items — by default dispatch `Agent(avengers-dev:thor)`; re-run
   `Skill(bmad-quick-dev)` in the main loop only when a fix needs user input —
   then dispatch Captain to re-review. Max 3 review cycles, then escalate to the user.
   Advance only on PASS, or CONDITIONAL PASS with no `[CRITICAL]`.
5. **Commit before Phase 9.** `bmad-quick-dev` commits its own work when the
   project is a git repo, but not in every case. Phase 9 measures committed
   history only, so confirm the quick-dev work (and any review fixes) is
   committed; if anything is left uncommitted, dispatch `Agent(avengers-dev:thor)`
   to commit it with a conventional message.
6. Phase 9 as in Step 5.

### 7. Phase Boundary Handling

At each main-loop phase completion, surface the boundary confirmation
(`§3.5`) in Vision's voice and wait for the user before advancing. For phases
with a verifying Avenger (1a, 4.5, 5, 8) and the Phase 7 build, IronMan relays the
Avenger's result, then advances. A Thor Blocked report is relayed to the user as
a question and never advanced past.

State file lives at `.avengers/relay-sequences/bmad-{name}.yaml` throughout.

### 8. md Commits (workstation only)

Offered at three points: after the Phase 1a stamp, at the hard gate, and at
completion (end of Phase 9, any track). Skip when `md_workstation` is `null`.
Relay-config §3.13 has the full rule.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-workstation/scripts/workstation.py md-status
```

Exit 2: the md folder is clean, or not a git repo — say nothing and continue.
Exit 1: note the error and continue. Exit 0: JSON `{toplevel, rel, dedicated,
repo_name, count, dirty}`. If `dedicated` is false — the md folder's git repo is
your home directory or a repo that contains this project — first warn plainly:
"The md folder is inside {toplevel}, which is not a dedicated md repo; a commit
there lands in that repo." Then ask: "Commit {count} md changes in {toplevel}?"

On yes, dispatch `Agent(avengers-dev:thor)` to run exactly, from any directory:
`git -C <toplevel> add -- ':(literal)<rel>'` then
`git -C <toplevel> commit -m "docs(<repo_name>): <phase> artifacts" -- ':(literal)<rel>'`
(`<phase>` is `discovery`, `design`, or `complete`). The pathspec commit leaves
anything else the user has staged in the md repo untouched. **Never push.** If a
hook or signing fails, report it and continue — an md commit never blocks the relay.
