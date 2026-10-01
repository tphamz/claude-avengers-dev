# BMAD Methodology Relay - Configuration

This is the configuration and protocol reference for the Avengers BMAD relay.
The relay **wraps the real BMAD-METHOD `bmad-*` skills** — it does not reimplement
them. Vision (the conductor) reads this at relay start to understand operational
parameters and the phase→skill+owner map.

## Relay Identity

- **Name:** BMAD — the Avengers relay that conducts the real BMAD-METHOD framework
  (mnemonic: *Build More Architect Dreams*). It orchestrates the installed `bmad-*`
  skills through the crew; it is not a competing methodology.
- **Type:** skill-wrapping, spec-driven methodology-relay
- **Phases:** 0 KB check, design 1a-5 (with 4.5 Spec Hardening), implementation
  6-8, 9 KB Refresh
- **Tracks:** `quick` | `standard` (default) | `full`
- **Conductor:** Vision agent (voice + map, not executor)

## Phase Map — phase → real skill → owner → tracks

Every wrapped skill except `bmad-dev-story` (and, on the full track,
`bmad-testarch-atdd`) runs **in the main loop** (Vision's voice), so the skill can
elicit from the user and write its artifacts; that includes Phase 7's
`bmad-create-story`. In Phases 1a, 4.5, 5 and 8 the owning Avenger is then
dispatched **read-only to verify** the result. In Phase 7 Thor runs
`bmad-dev-story` (after `bmad-testarch-atdd` on the full track) to build, and the
main loop relays each of its HALTs to the user (`§3.12`).

| Phase | Real skill(s) | Owner | Tracks |
|-------|---------------|-------|--------|
| 0 KB check | `bmad-kb.py status` | main loop | all |
| 1a Discovery (conditional) | `bmad-document-project` + `bmad-generate-project-context`, then `bmad-kb.py stamp` | main loop (Vision voice); `Agent(avengers-dev:blackwidow)` verifies | standard, full |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | standard, full |
| 2 PRD | `bmad-prd` create; optional validate / `bmad-advanced-elicitation` | main loop (Vision voice) | standard, full |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | standard, full |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | standard, full |
| 4.5 Spec Hardening | `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` | main loop; `Agent(avengers-dev:captain)` (`adversarial` lens) verifies and assigns severity | standard, full |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | standard, full |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | standard, full |
| 7 Build (per story) | `bmad-create-story` → `bmad-testarch-atdd` (full only) → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-testarch-atdd` (full only) and `bmad-dev-story` per story (HALTs relayed) | standard, full |
| 8 Review | `bmad-code-review` + `bmad-testarch-trace` (full only) + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | standard, full |
| 9 KB Refresh | `bmad-kb.py impact` → `bmad-document-project` + `bmad-generate-project-context` → `stamp` | main loop (Vision voice) | all |
| Quick track | `bmad-quick-dev`, then Captain reviews the diff | main loop, then `Agent(avengers-dev:captain)` | quick |

Per-phase stubs: `phase-0-kb.md`, `phase-1-assessment.md` … `phase-8-review.md`,
`phase-4.5-hardening.md`, `phase-9-kb-refresh.md`, and `track-quick.md`.

**Why the split:** the wrapped `bmad-*` skills halt for user input and write
artifacts step by step; `bmad-code-review` also spawns its own subagents. A
subagent runs blind and cannot elicit, and BlackWidow, Hulk and Captain have no
Write, Edit or Agent tools. So the skills run in the main loop (`§3.10`) and those
owners verify the output read-only. `bmad-dev-story` and `bmad-testarch-atdd`
change source code, so they run in Thor, who returns a Blocked report whenever
one stops for a human. The main loop may read broadly and write BMAD artifacts
and relay bookkeeping (the full list is `§3.10`), but never modifies source code
— code changes (including code-review patches) always go to Thor. **Quick-track
exception:** on the quick track, `bmad-quick-dev` runs in the main loop and
implements the code; it is the one sanctioned case where the main loop writes
source code. Captain's fixes on the quick track still go to Thor by default
(`§3.10`).

<!-- SEAM: A main-loop phase could later move to a write-capable subagent if its
     wrapped skill gains a batch mode. Never move one to a read-only agent, and
     never while the skill still asks the user questions. -->

## State File

Location: `.avengers/relay-sequences/bmad-{name}.yaml`

### State Schema

```yaml
sequence_id: string           # Unique identifier: bmad-{name}
name: string                  # Human name: {name}
status: enum                  # active | suspended | complete | closed | abandoned
track: enum                   # quick | standard | full   (missing -> standard)
current_phase: string         # 0 | 1a | 1b | 2 | 3 | 4 | 4.5 | 5 | 6 | 7 | 8 | 9
                              # (quick track: 0 | quick-dev | review | 9)
                              # new sequences start at 0
design_implementation_boundary_passed: bool  # Phase 5->6 hard gate
gate_override:                # null, or set when the gate is passed despite blockers
  reason: string              #   user-supplied reason (required)
  at: timestamp
kb_status_at_start: enum      # missing | unstamped | fresh | stale | unknown (Phase 0)
kb_base_commit: string | null # HEAD at Phase 0; base for Phase 9 impact
md_workstation: string | null # md workstation path from Step 0 (§3.11); null = in-repo
created_at: timestamp
last_active: timestamp

relay_modifiers:
  existing_code_in_scope: bool   # Brownfield mode (drives Phase 1a skill choice)

loop_state:                      # Phases 7 and 8
  total_items: int
  completed: list                # story keys whose Phase 7 step 5 finished (phase7_step: recorded);
                                 # read by marker inference and the §3.13 step 8 scope check,
                                 # never a resume skip rule (§3.2)
  in_progress: string | null     # story key of the dispatch that last started (§3.12 step 2)
  remaining: list
  retros_declined: list          # epic numbers (strings) the user skipped (§3.13 step 8)
  phase8_start_sha: string       # HEAD at Phase 8 entry, written once (or NO_VCS)
  stories:                       # per story key (story file name without .md)
    <story_key>:
      phase7_step: enum          # pending | dispatched | done_reported | recorded (§3.12, §3.2)
      phase8_step: enum          # pending | code_review_done | fixing | captain | verify | closed
                                 # (§3.13, §3.2)
      baseline_commit: string    # Phase 7 chain start: pre_sha of the first dev-story dispatch,
                                 # written before that dispatch, never overwritten (or NO_VCS)
      phase7_end_sha: string     # post_sha of the Phase 7 dispatch that reported done,
                                 # never overwritten (or NO_VCS)
      chain_start_sha: string | null  # Phase 8 fix chain start: pre_sha of the chain's first
                                 # dispatch, written before it; null once the fix range is recorded
      phase8_fix_ranges: list    # one <chain_start_sha>..<done post_sha> per Phase 8 fix (or NO_VCS)
      trace_report: string | null  # full track: path of the bmad-testarch-trace report for this
                                 # story, written with code_review_done (§3.13); null otherwise
      review_cycles: int         # Captain verdicts so far in Phase 8 (max 3, §2.10)
      captain_findings: string | null  # latest Captain verdict + findings, written with
                                 # review_cycles; read by a resume at phase8_step: verify
      blocked:                   # set while Thor's last report was Blocked (§3.12), else null
        halt_point: string       # skill step or file:line where dev-story stopped
        question: string         # what dev-story needs from the user
        options: string          # the choices Thor reported
        work_state: string       # Thor's Work state: uncommitted files, tests run, committed: NO
        resume_instruction: string  # Thor's Resume instruction for the re-dispatch
        dispatched_at_sha: string  # pre_sha of the Blocked dispatch itself (informational;
                                 # the chain start is baseline_commit or chain_start_sha)
```

Every SHA and range above is recorded by the main loop from `git rev-parse HEAD`
(`§2.9`), never from the SHA in Thor's report.

Every change to `phase7_step` or `phase8_step` is written to the state file
immediately, together with any other field changed in the same step (so a crash
never leaves a marker ahead of, or behind, the data it describes).

**Legacy state files:** an older `phase8_fix_shas` list (one commit SHA per fix)
is read as the ranges `<sha>^..<sha>` and written back as `phase8_fix_ranges`.

**Marker inference (legacy and untracked stories).** Runs every time the state
file is read (on resume, and at Phase 7 and Phase 8 entry), before any phase
entry step and before any loop. It covers every story key in the
`sprint-status.yaml` `development_status` list, including keys with no
`loop_state.stories` entry (for example, stories built by an earlier BMAD
sequence). Epic keys (`epic-N`, `epic-N-retrospective`) are excluded. An
absent field counts as empty or 0. The inferred markers are written back to the
state file in one write.
- **No `phase7_step`:** `dispatched` if it has
  `loop_state.stories[<key>].baseline_commit` (a `baseline_commit` in the story
  frontmatter alone does not count), no `phase7_end_sha`, is not in
  `loop_state.completed`, and its `development_status` entry is not `done`
  (tested first, so a crashed dispatch goes through the `§3.2` recovery and its
  checks). A `done` story that has a `loop_state` `baseline_commit` but no
  `phase7_end_sha` and no `completed` entry is never inferred `dispatched` and
  never re-dispatched: ask the user which Phase 7 step it reached. Else
  `recorded` if the key is in
  `loop_state.completed`, or its `development_status` entry is `review` or
  `done`, or it has a `phase7_end_sha`; else `pending`. A story inferred as
  `recorded` may have no `phase7_end_sha`; Phase 8 then builds its range with
  the `§2.9` resume fallback.
- **No `phase8_step`:** `closed` if its `development_status` entry is `done`
  (such a story is never set to `pending`); else `pending` if it has no
  `phase8_fix_ranges` and `review_cycles` is 0; for any other story, ask the
  user which Phase 8 step it reached.

The Phase 8 entry step (`§3.13`) runs after inference and sets `pending` only on
stories still unmarked.

Artifact paths are owned by the wrapped `bmad-*` skills (BMAD-METHOD writes under
its configured `output_folder` and `project_knowledge`) and resolved from
`_bmad/bmm/config.yaml` (see `§2.8`) — the relay does not dictate them. With an md
workstation, `output_folder` is a symlink into it (`§3.11`).

## Protocol Directives

### §2.2 Close-Out Dialogue

When user says 'stop' during any phase:
1. Save current state to disk
2. Ask: "Save and suspend (resume later) or close out permanently?"
3. `suspended` = paused, resume available
4. `closed` = user is done; artifacts preserved but relay inactive

### §2.5 No Role-Play

Operate as Vision's functional persona — do not role-play as human characters.
The wrapped `bmad-*` skills bring their own domain personas; the relay narration
stays in Vision's voice.

### §2.7 Deterministic-First

Readiness (Phase 5) runs `bmad-check-implementation-readiness` in the main loop;
its report carries a status of READY / NEEDS WORK / NOT READY. Hulk then gives an
independent verdict (READY / READY-WITH-CONCERNS / NOT-READY) on that report. The
gate shows **both**. If either is NOT READY / NOT-READY, IronMan recommends [2]
Exit. If either is NEEDS WORK / READY-WITH-CONCERNS, IronMan flags it explicitly
and lists the cited gaps. In every case the user decides. Neither verdict
auto-advances or auto-blocks the gate; a NOT READY / NOT-READY result only makes
[1] require an override (`§3.9`).

### §2.8 Artifact Path Resolution

Before dispatching a verifying Avenger, the main loop reads
`_bmad/bmm/config.yaml`, substitutes `{project-root}`, and passes **concrete file
paths** — never globs or unresolved `{placeholders}`. Keys and installer defaults:

| Key | Default | Written there |
|-----|---------|---------------|
| `project_knowledge` | `docs` | `bmad-document-project` output |
| `planning_artifacts` | `_bmad-output/planning-artifacts` | `implementation-readiness-report-{date}.md` (pass the newest file) |
| `implementation_artifacts` | `_bmad-output/implementation-artifacts` | story files, `sprint-status.yaml`, `deferred-work.md`, `epic-{N}-retro-{date}.md` |
| `output_folder` | `_bmad-output` | `project-context.md` (`bmad-generate-project-context`) |

Phase 8 also needs, per story: the story file path, its `loop_state.stories`
entry (the review ranges are `<baseline_commit>..<phase7_end_sha>` plus each range
in `phase8_fix_ranges`, all recorded from HEAD per `§2.9`; never `..HEAD`, which
includes later stories), and its story key (the story file name without `.md`,
e.g. `1-2-user-auth`) for the close-out write to `sprint-status.yaml`. See
`references/bmad/phase-8-review.md`.

### §2.9 Commit Range Recording (from git HEAD)

Thor's report has a single `**Commit**` field, and one run can make several
commits, so the relay never builds a range from the SHA Thor reports. The main
loop records every SHA itself:

- **`pre_sha` / `post_sha`.** Immediately before every Thor dispatch, run
  `git rev-parse HEAD` and keep the result as `pre_sha`. Immediately after his
  report, run it again for `post_sha`. If either call fails (unborn HEAD), use
  the empty-tree hash (see **Unborn HEAD** below).
- **Dispatch chain.** One unit of Thor work (a story's Phase 7 build, or one
  Phase 8 fix) may take several dispatches: Blocked re-dispatches (`§3.12`),
  agent-failure retries, and the commit follow-up of check 3. Its range runs
  from the chain start to the `post_sha` of the dispatch that reports done:
  `<chain start>..<done post_sha>`. The chain start is the `pre_sha` of the
  chain's first dispatch, and it is **written to the state file before that
  dispatch**: `baseline_commit` for a Phase 7 build, `chain_start_sha` for a
  Phase 8 fix. Clearing `blocked` never touches either field, so a resume after
  any number of Blocked reports still has the chain start.
- **Phase 7.** `baseline_commit` is the `pre_sha` of the story's first
  dev-story dispatch, written before it. If the story already has a
  `baseline_commit` in `loop_state`, keep it; never overwrite it. Cross-check it
  against the `baseline_commit` that `bmad-dev-story` step 4 writes to the story
  frontmatter; if they differ, tell the user and keep the relay's value.
  `phase7_end_sha` is the `post_sha` of the dispatch that reports the story done;
  once written it is never overwritten.
- **Phase 8.** Before the first dispatch of each fix chain, write its `pre_sha`
  as the story's `chain_start_sha` (if `chain_start_sha` is already set, the
  chain is resuming; keep it). On the done report, append
  `<chain_start_sha>..<done post_sha>` to `phase8_fix_ranges`, then set
  `chain_start_sha` to null. `phase8_start_sha` is `git rev-parse HEAD` run once
  at Phase 8 entry, before any Phase 8 dispatch; it is never overwritten,
  including on resume.
- **Checks after each done report** (never after a Blocked report, and none of
  them run under `NO_VCS`), on the chain range `<chain start>..<post_sha>`:
  1. `post_sha == <chain start>` → flag to the user that nothing was committed.
  2. `git merge-base --is-ancestor <chain start> <post_sha>` fails → history was
     rewritten; stop and ask the user.
  3. Uncommitted story work. Run
     `git status --porcelain -z --untracked-files=all` (NUL-separated, so paths
     are never quoted). Its paths are relative to the repository root. A rename
     or copy entry carries a second NUL-terminated path, the original; both
     paths count. Flag only the paths that also appear in the story's File List
     or in Thor's reported Files Changed or Work state (only the File List when
     the chain's reports are lost in a `§3.2` resume recovery). If the BMAD project root
     is a subdirectory of the repository, the main loop first prefixes each File
     List path with that subdirectory (`git rev-parse --show-prefix`, run from
     the project root) so both sides are repo-root-relative. Every other path is
     ignored, including the relay state file `.avengers/relay-sequences/*`,
     anything under `{planning_artifacts}` or `{implementation_artifacts}`, and
     an untracked `_bmad/`. A flagged path is work the range would miss: tell the
     user and dispatch Thor to commit exactly those paths. That dispatch is part
     of the same chain (it keeps the chain start). After its report, take
     `post_sha` again; it replaces the earlier `post_sha` as the chain's end.
     Rerun the checks on it and record it. If check 3 still flags, stop and ask
     the user.
  4. Unreported commits. Compare `git log --oneline <chain start>..<post_sha>`
     against every commit Thor reported across the whole chain: each Blocked
     re-dispatch, each agent-failure retry, the check-3 follow-up and the done
     report. Flag to the user only the commits that no report mentioned. When
     the chain's reports are lost (a `§3.2` resume recovery), there is nothing
     to compare against: list the chain's commits to the user instead.
- **Unborn HEAD.** In a git repository with no commits yet, `git rev-parse HEAD`
  fails; use the empty-tree hash for that `pre_sha` or `post_sha`. Compute it
  with `git hash-object -t tree /dev/null` rather than hardcoding it, because it
  depends on the repository's hash algorithm. (Note: in a SHA-1 repository it
  is `4b825dc642cb6eb9a060e54bf8d69288fbee4904`.) **This is the one rule for an
  empty-tree left side**, used by every range consumer (Phase 8 code review,
  Captain, BlackWidow, the checks above, the resume fallback). When a range's
  left side is the empty-tree hash `<empty-tree>`:
  - diff it with `git diff <empty-tree> <sha>`;
  - list its commits with `git log --oneline <sha>`;
  - skip `git merge-base --is-ancestor` (check 2, and that link of the resume
    fallback's chain).
  dev-story may write `NO_VCS` to the frontmatter in this case. In a git
  repository a frontmatter `NO_VCS` is ignored: the cross-check skips it, and the
  resume fallback uses `loop_state` or the empty-tree hash instead.
- **NO_VCS.** Only a project that is not a git repository
  (`git rev-parse --is-inside-work-tree` fails) records `NO_VCS` for every SHA
  and range. Captain and BlackWidow then review the story's File List as the
  files stand now, and Thor reports "no commit (NO_VCS)".
- **Resume fallback.** If `loop_state.stories` has no `phase7_end_sha` for a
  story, take its `baseline_commit` from `loop_state` if recorded, else from the
  story frontmatter (a frontmatter `NO_VCS` in a git repository → the empty-tree
  hash). Its end is the next story's `baseline_commit`, in `development_status`
  order in `sprint-status.yaml`; the last story's end is `phase8_start_sha`.
  Each baseline must be an ancestor of the next (`git merge-base
  --is-ancestor`), except that a link whose left side is the empty-tree hash
  skips the check. If the stories are not in build order or the baselines do not
  chain, stop and ask the user for the ranges.

### §2.10 Review Cycles

`review_cycles` counts Captain verdicts for a story in Phase 8. It starts at 0
and goes up by 1 after each Captain verdict, and the main loop writes it to the
state file immediately, so a resume never repeats or skips a cycle. The first
Captain review is cycle 1. After the verdict of cycle 3, a story that has not
passed goes to the user. Thor dispatches, Blocked re-dispatches, agent-failure
retries and BlackWidow verifications do not change the count. This is the same limit as CLAUDE.md
Feature Implementation step 7 ("max 3 cycles") and `personas/ironman.md` Quality
Gate step 4 ("Maximum 3 review cycles"): one cycle is one Captain verdict.

### §3.2 Resume Protocol

On resume, read the state file first. Surface to user:
> "Resuming BMAD '{name}' at Phase {N}: {phase-name} ({context})."

Re-enter at `current_phase`, respecting `design_implementation_boundary_passed`.

**Resume defaults.** A **legacy state file** is one with **no `track` key**
(written before tracks and Phases 0/4.5/9 existed). For legacy files only:

- `track` → `standard`.
- At `8` or `complete` → finish as before; **not** routed into Phase 9.
- Otherwise → continue through Phase 9. With no `kb_base_commit`, Phase 9 uses the
  `stamped_commit` reported by `bmad-kb.py status`; if there is none, Phase 9 is
  skipped with a note.
- Missing `gate_override` → `null`.

State files with a `track` key follow the normal flow, including Phase 9.

On a resume into Phase 7 or 8, in this order. Resume decisions come from the
per-story markers `phase7_step` and `phase8_step`, never from
`loop_state.completed` or a `development_status` value alone (every story is in
`completed` once Phase 7 ends). Those two are read by marker inference
(State Schema), which runs first, when the state file is read, and fills in the
markers of stories that have none; `completed` is also read by the `§3.13`
step 8 scope check. Neither drives a resume decision.

1. **Suspended Blocked stories first.** If any `loop_state.stories` entry has a
   `blocked` entry, replay it to the user before any dispatch: the stored
   `halt_point`, `question`, `options` and `work_state`. Ask one plain question:
   answer, or keep it suspended. Keep suspended → leave `status: suspended` and
   stop. Answer → continue at `§3.12` step 4's answer path: add the `[Gate]`
   subtask and do the status reset where they apply, clear `blocked`, and
   re-dispatch Thor with the answer, the stored `work_state` and the stored
   `resume_instruction`. The chain start is the recorded `baseline_commit`
   (Phase 7) or `chain_start_sha` (Phase 8), never a new `pre_sha`. When the
   replayed chain reports done:
   - **Phase 7 chain:** continue at `§3.12` step 5 (which first sets
     `phase7_step: done_reported`).
   - **Phase 8 fix chain:** run the `§2.9` checks on
     `<chain_start_sha>..<post_sha>`, append that range to `phase8_fix_ranges`,
     set `chain_start_sha` to null and `phase8_step: captain` (one state write),
     and continue at Phase 8 step 4 (Captain, `§3.13`).
2. **Orphaned Phase 8 fix chain.** For a story with `chain_start_sha` set,
   `blocked` null and `phase8_step: fixing`, a fix chain started and never
   reported. Show the user `git log --oneline <chain_start_sha>..HEAD` and
   `git status`, and ask one plain question: re-dispatch Thor to finish the fix,
   or treat the chain as done.
   - **Finish:** keep `chain_start_sha`, record a new `pre_sha`, and dispatch
     Thor as in Phase 8 step 3 with the still-unchecked `[Review][Patch]` and
     `[Gate]` items; the chain continues from there.
   - **Done:** take `post_sha` = `git rev-parse HEAD` now, run the `§2.9` checks
     on `<chain_start_sha>..<post_sha>`, then record that range exactly as the
     Phase 8 replay above does and continue at Phase 8 step 4. Tell the user the
     range was recovered from HEAD.
3. **Then the loop for the resumed phase.**
   - **Phase 7 (`§3.12` loop).** Skip a story only when `phase7_step: recorded`.
     - `pending` → start at `§3.12` step 1.
     - `done_reported`, or `dispatched` with no `blocked` where the story's
       `development_status` entry is `review` → a done report arrived (or
       dev-story finished) before step 5 was written. Take `post_sha` =
       `git rev-parse HEAD` now, run the `§2.9` checks on
       `<baseline_commit>..<post_sha>` (Thor's reports are lost, so checks 3
       and 4 use their lost-reports form), then do
       `§3.12` step 5. Tell the user the range was recovered from HEAD.
     - `dispatched` with `blocked` → handled by step 1 above.
     - `dispatched` with no `blocked` and the story not at `review` → the
       dispatch was interrupted with no report. Tell the user, show
       `git status`, and re-dispatch at `§3.12` step 2 as an agent-failure retry
       (the recorded `baseline_commit` is kept).
   - **Phase 8 (`§3.13` loop).** Keep the recorded `phase8_start_sha`, and
     rebuild any missing story ranges with the `§2.9` resume fallback. Skip a
     story only when `phase8_step: closed`. Otherwise re-enter at the recorded
     step:
     - `pending` → step 1, code review.
     - `code_review_done` or `fixing` → step 2 (reconcile) only if it is not
       already done, then step 3 (Thor) if unchecked `[Review][Patch]` or
       `[Gate]` items remain, otherwise step 4. (A `fixing` story with
       `chain_start_sha` set is handled by step 1 or step 2 above first.)
       **Full track, at `code_review_done`:** before step 2, if `trace_report`
       is recorded, read that report and, for each untested AC in it with no
       matching `[Review][Patch] Cover AC <n>:` bullet (checked or unchecked) in
       the story's `### Review Findings`, re-derive the bullet from the report
       exactly as Phase 8 step 1 writes it (`§3.13`). The trace never re-runs.
     - `captain` → step 4, Captain.
     - `verify` → step 5, BlackWidow, with the stored `captain_findings`.
     - After the loop, run the epic close-out sweep of `§3.13` step 8: the
       epic sweep (set `epic-N: done` for every complete epic whose `epic-N`
       entry is not `done`), then the retrospective offer for each owed epic.
   - Never re-run code review on a story past `pending`. Never set a `closed`
     story back to `in-progress`. Carry `review_cycles` over unchanged.

### §3.5 Phase Boundary Confirmation

Each interactive phase announces completion and waits for user confirmation before
advancing. Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"
Phases with a verifying Avenger (1a, 4.5, 5, 8) and the Phase 7 build report through
that Avenger; IronMan relays, then advances. A Thor Blocked report is relayed as a
question to the user (`§3.12`), never advanced past.

### §3.6 Design-Implementation Boundary (Hard Gate)

The boundary between Phase 5 and Phase 6 is a hard gate. User must explicitly choose:
- [1] Continue into implementation
- [2] Exit (artifacts saved, relay suspended)

No auto-advance. No batch-through. Set `design_implementation_boundary_passed: true`
only on [1]. The gate reads both readiness results (`§2.7`): the report status
and the verdict **Hulk returns**, not the file alone. If either is NOT READY /
NOT-READY, or Phase 4.5 left `[CRITICAL]` findings unresolved, [1] requires an
override (§3.9).

### §3.7 Scope Creep Prevention

During Phase 7, if implementation surfaces out-of-scope requirements:
- Surface to user with three options (note/defer, pause-replan, add-informally)
- Do not implement out-of-scope items silently

### §3.8 KB Lifecycle

The knowledge base (KB) is two files produced by the real BMAD skills, at paths
read from `_bmad/bmm/config.yaml` (falling back to `_bmad/core/config.yaml`, then
defaults `docs` / `_bmad-output`):

- `{project_knowledge}/index.md` — `bmad-document-project`
  (`initial_scan` | `full_rescan` | `deep_dive`)
- `{output_folder}/project-context.md` — `bmad-generate-project-context`

The freshness marker is `<workstation>/avengers/kb.json` with an md workstation,
else `.avengers/kb.json`; reads fall back to the legacy `.avengers/kb.json` and
`stamp` moves it into the workstation. Schema:
`{version: 2, index_path, context_path, branches: {<branch>: {commit, stamped_at,
arch_hashes}}}` — keyed per branch so worktrees on different branches do not
overwrite each other (detached HEAD uses `HEAD@<sha7>`). A branch with no entry
falls back to the newest entry and reports `stale` with a `branch_unstamped`
signal. Paths are relative to the workstation (in-repo paths as
`{project-root}/...`). Read the marker through `bmad-kb.py status`, not by path.

- **Build only when missing** — Phase 0 `status` = `missing` → Phase 1a.
- **Offer refresh when meaningfully stale** — `stale` means at least one impact
  signal since the stamp (breaking-change commit, architecture doc under the output
  folder, dependency manifest, migration, API contract, new top-level dir) or 20+
  changed files outside the KB dirs, `output_folder`, `.avengers/`, and `_bmad/`.
  An `unknown_stamp` signal (the stamped commit is no longer in history, e.g.
  rebased away) also makes the KB `stale`. When the output folder is outside git
  (an md workstation), architecture docs are compared by the sha256 hashes stored
  at stamp time instead of by git diff. The user decides.
- **Not a git repo** — `status` reports `unknown` (or `unstamped` with a null
  `head`); `stamp` and `impact` exit 1, so they are skipped and freshness is not
  tracked.
- **Refresh at the end when the change is important or breaking** — Phase 9 runs
  `impact --base <kb_base_commit>`; if `refresh_recommended`, the user confirms,
  then `deep_dive` per area (3 or fewer `changed_areas`) or `full_rescan`, then
  `bmad-generate-project-context`, then `stamp`.

### §3.9 Gate Override

When either readiness result is NOT READY / NOT-READY (`§2.7`), or Phase 4.5
`[CRITICAL]` findings are unresolved, a bare [1] at the gate is refused. The user must type `override` plus a reason. Record
`gate_override: {reason, at}` in the state file and set
`design_implementation_boundary_passed: true`.

### §3.10 Wrapped Skills Run in the Main Loop

Every wrapped skill runs in the main loop via `Skill(bmad-X)` — including
`bmad-document-project` and `bmad-generate-project-context` in Phases 1a and 9
(and in the scheme KB Sync phases, item 3 below), the Phase 4.5 review skills,
and `bmad-quick-dev` on the quick track — except the code-writing skills Thor runs (`bmad-dev-story` in Phase 7 and Phase 8 step 3,
and `bmad-testarch-atdd` in Phase 7 on the full track). Read-only Avengers are
dispatched only to verify a skill's output (1a, 4.5, 5, 8), never to run a
write-capable skill.

**Main-loop writes (canonical list).** Other files point here. The main loop
may write only:

1. **BMAD artifacts**, while running a wrapped skill and in the relay steps
   around it: the Phase 7 epic-status write before `bmad-create-story`, the
   Blocked resets (`[Gate]` subtask, story and `sprint-status.yaml` back to
   `in-progress`), the Phase 8 `Cover AC` bullets from the trace, Review
   Findings reconciliation, appended Captain findings, close-out, and the
   Phase 8 epic `done` write at epic completion (step 8, and the epic sweep
   before Phase 9).
2. **Relay bookkeeping:** the relay state file
   `.avengers/relay-sequences/bmad-{name}.yaml`; the `bmad-kb.py stamp` outputs
   (`kb.json`, in the workstation or `.avengers/`, and
   `.claude/rules/avengers-kb.md`); and the `workstation.py set` symlink repair
   at Step 0 (`§3.11`).
3. **Scheme KB Sync** (the `avengers-assemble` and `rescue-mission` KB Sync
   phase, outside `/bmad`): the KB docs that `bmad-document-project` and
   `bmad-generate-project-context` write when run in the main loop, and the
   `bmad-kb.py stamp` outputs from item 2. IronMan also runs `bmad-kb.py status`
   and `impact` and the read-only `workstation.py md-status`. The repo KB commit
   and the md commit (`§3.11`, `<phase>` = `kb-sync`) go to Thor; as generated
   documentation they need no Captain review.

It never modifies source code: code changes, including code-review patches,
always go to Thor. **Quick-track exception:** on the quick track,
`bmad-quick-dev` runs in the main loop and implements the code; it is the one
sanctioned case where the main loop writes source code. In the quick-track fix
loop, Captain's fixes go to Thor by default; re-run `bmad-quick-dev` in the main
loop only when a fix needs user input.

### §3.11 md Workstation and md Commits

**Step 0 (every run):** after preflight, `workstation.py resolve`. `ok` continues
(a missing or mismatched symlink is repaired with `set`); `in_repo` continues
in-repo; `guess` / `missing` / `broken` run the `/avengers-workstation` flow, where
the user may still choose in-repo. Then `workstation.py check-config` (exit 1 — `_bmad/`
missing or `output_folder` outside the project — is reported and skipped): keys
outside `output_folder` are offered for an opt-in, per-key `repoint-config` (it edits the
team's committed config — say so). Declined keys are recorded in
`.avengers/settings.json` → `mdRepointDeclined` and not offered again. It runs on
every run because a BMAD reinstall can undo a re-point and a symlink can dangle.
Record `md_workstation` in the state file.

**md commits:** offered after the Phase 1a stamp, at the hard gate, and at
completion (end of Phase 9, any track), only when `md_workstation` is set. The
scheme KB Sync phases offer the same md commit with `<phase>` = `kb-sync`.
The workstation folder is `<md-root>/<repo-name>-mds/`.

1. `workstation.py md-status` — exit 2 (clean, or not a git repo): skip silently.
2. Exit 0: if `dedicated` is false (the md repo is `$HOME` or contains the project),
   warn first that the commit lands in that repo. Then ask "Commit N md changes in
   <md repo>?"
3. On yes, Thor runs `git -C <toplevel> add -- ':(literal)<rel>'`, then
   `git -C <toplevel> commit -m "docs(<repo-name>): <phase> artifacts" -- ':(literal)<rel>'`.
   The pathspec commit leaves anything else staged in the md repo untouched.
4. A hook or signing failure is reported and the relay continues. Never push.

The spec-commit gate in `agents/thor.md` is deliberately stricter than this KB/phase
md-commit gate: spec commits refuse a non-dedicated md repo outright, where KB/phase
commits warn and ask.

**Known limitation:** `bmad-story-automator` rejects artifact paths that resolve
outside the repo root, so it does not work with a workstation. The relay's Phase 7
(the main loop running `bmad-create-story`, Thor running `bmad-dev-story`) does
not use it.

### §3.12 Phase 7 Per-Story Sequence and Blocked Relay

For each story, in `development_status` order in `sprint-status.yaml`. **Skip
a story** only when its `phase7_step` is `recorded`. Every other value is
re-entered as `§3.2` step 3 (Phase 7) says; a suspended Blocked story is
handled by `§3.2` step 1 before the loop. Marker inference (State Schema) has
already run when the state file was read, so a story at `review` or `done` in
`sprint-status.yaml` with no `loop_state.stories` entry (for example, from an
earlier sequence) is `recorded` and skipped. A story with nothing to infer from
starts at `phase7_step: pending`.

1. **Create the story (main loop).** Skip this step if the story's
   `development_status` entry is already past `backlog`. Otherwise check the
   epic's entry (`epic-N`) first: `backlog` or `contexted` → set it to
   `in-progress` (given an explicit key, `bmad-create-story` does not);
   `in-progress` → no change; `done` → stop and ask the user; anything else →
   stop. Then run `Skill(bmad-create-story)` with the full `development_status`
   key (e.g. `1-2-user-auth`, not `1-2`); a short key misses the entry at its
   step 6, and dev-story step 4 then never writes `baseline_commit`. The user
   answers its checklist menu and any missing-input offer; the main loop runs its
   web-research step. Afterwards, verify that the story file's `Status` and its
   `sprint-status.yaml` entry are both `ready-for-dev`; if not, stop and tell the
   user.
2. **Record `pre_sha`** (`§2.9`) and resolve the story file path
   (`{implementation_artifacts}/<story_key>.md`). Set `loop_state.in_progress`
   to the story key; this happens at the start of every dispatch, re-dispatches
   and Phase 8 fixes included. If the story has no `baseline_commit` in
   `loop_state` yet, write this `pre_sha` as its `baseline_commit`. Set
   `phase7_step: dispatched` and save the state file **before** dispatching.
   Never overwrite an existing `baseline_commit`.
3. **Build (Thor).** Dispatch `Agent(avengers-dev:thor)` to run
   `bmad-dev-story` on the explicit story file path, with this instruction: at
   any dev-story HALT or ask point, do not guess and do not work around it — stop
   without committing and return a Blocked report (`agents/thor.md`). dev-story's
   step-10 completion explanation and next-step prompts are not stops: finish,
   run tests, commit, and report done. **Full track only:** in the same dispatch,
   before dev-story, Thor runs `bmad-testarch-atdd` on the story (failing
   acceptance tests from its ACs; skipped on a re-dispatch once those tests
   exist), under the same HALT instruction, so its tests fall inside the story's
   chain range.
4. **Blocked.** Record `post_sha` and write
   `loop_state.stories[<story_key>].blocked` = `{halt_point, question, options,
   work_state, resume_instruction, dispatched_at_sha}`: the first five from
   Thor's report, `dispatched_at_sha` from that dispatch's `pre_sha`. Save the
   state file. Show
   the user the HALT point, the question, the options and the work state, and ask
   one plain question: answer, or suspend (`status: suspended`, state saved). On
   an answer, before re-dispatching:
   - **Step-9 gate HALT for regression or definition-of-done failures:** every
     task is already checked, so a plain re-dispatch jumps straight back to
     step 9 and fails the same way, and dev-story does no work that no task maps
     to. Append an unchecked `- [ ] [Gate] Fix <failure>: <user answer>` subtask
     at the end of `## Tasks / Subtasks`. No `[Gate]` subtask for the other two
     step-9 HALTs: for "any task is incomplete", the unchecked task already sends
     dev-story back to work on re-dispatch; for "File List is incomplete", tell
     Thor to fix the File List directly.
   - **Status reset.** If dev-story had already set `review` (step 9 runs before
     its final gates), set the story file's `Status` and its `sprint-status.yaml`
     entry back to `in-progress`.
   - **Re-dispatch.** Clear `blocked` (the chain start stays in
     `baseline_commit`, or `chain_start_sha` in Phase 8), record a new
     `pre_sha`, and dispatch Thor again with the user's answer, the previous
     Work state (the uncommitted files, to carry forward rather than redo or
     discard) and the Resume instruction. Every re-dispatch after a Blocked report
     carries all three. This loop has no cap, because the user answers each
     time. A real agent failure (no report, or a crash) still follows the retry
     rule: up to 2 retries, then escalate.
5. **Done.** As soon as a done report arrives, set `phase7_step: done_reported`
   and save the state file, before any check. Then record `post_sha` and run the
   `§2.9` checks on `<baseline_commit>..<post_sha>` (check 3 may add a commit
   dispatch to the same chain and a new `post_sha`). Cross-check
   `baseline_commit` against the story frontmatter, then write `phase7_end_sha`
   (the final `post_sha`) to `loop_state.stories[<story_key>]` unless one is
   already recorded. Add the key to `completed`, set `in_progress` to null,
   update `remaining`, and set `phase7_step: recorded`, all in one state write.

Phase 8 step 3 (Thor resolving `[Review][Patch]` items) uses the same Blocked
handling as step 4 here: the stored `blocked` fields, the relay, the `[Gate]`
subtask for regression or definition-of-done HALTs, the status reset, and
re-dispatches that carry the answer, Work state and Resume instruction. Step 5
here does not apply to it: a Phase 8 fix chain's done report continues at
Phase 8 step 3's done path (`§3.13`: the `§2.9` checks, the fix range, then
Phase 8 step 4, Captain). Its chain start is `chain_start_sha`, written before
the chain's first dispatch, and its fix range `<chain_start_sha>..<done post_sha>`
spans the whole chain. Blocked re-dispatches never count toward `review_cycles`.

### §3.13 Phase 8 Per-Story Progress Markers

Full step detail lives in `references/bmad/phase-8-review.md`; this section
fixes when `phase8_step` changes. Each change is written to the state file
immediately, in the same write as the data that step produced.

- **Entry.** Marker inference (State Schema) has already run when the state
  file was read. With `phase8_start_sha`, set `phase8_step: pending` only on
  stories still unmarked after inference. A story whose `development_status`
  entry is `done` was inferred `closed` and is never set to `pending`.
- **Step 1, code review.** Runs only at `pending`. Standard track: when the user
  picks "Done" at its next-steps menu → `code_review_done`. **Full track:**
  after "Done", run `bmad-testarch-trace` for the story in the main loop, before
  any marker change. Right after it, the main
  loop writes every AC the trace reports untested into the story's
  `### Review Findings` (inside `## Tasks / Subtasks`; create the subsection
  there if code review wrote none) as an unchecked
  `- [ ] [Review][Patch] Cover AC <n>: <AC text, short>` bullet, skipping any
  `Cover AC <n>` bullet already present. Then, in one state write, it records
  `loop_state.stories[<key>].trace_report: <report path>` and sets
  `code_review_done`. Recording the report path is what lets a resume re-derive
  lost bullets (`§3.2`).
- **Step 2, reconcile.** Trace output is never converted here; step 1 already
  wrote the `Cover AC` bullets, and step 2 only dedupes against them (a
  converted decision that duplicates a `Cover AC` bullet is not added again).
  Already done when the story's `### Review Findings`
  (if code review wrote one) sits inside `## Tasks / Subtasks` and has no
  unchecked `[Review][Decision]` bullet, and the story's `sprint-status.yaml`
  entry is `in-progress`; skip it then. Before that check, merge duplicate
  `### Review Findings` sections (a re-run code review appends a second one)
  into one, keeping each bullet once. On a resume at `code_review_done` with
  unchecked `[Review][Decision]` bullets, the code-review conversation is lost:
  ask the user to decide each one directly, then reconcile as usual. After it:
  unchecked `[Review][Patch]` or `[Gate]` items → step 3; none → `captain`.
- **Step 3, fix (Thor).** Before the chain's first dispatch → `fixing`, in the
  same write as `chain_start_sha`. On the done report: the `§2.9` checks, then
  append the fix range, set `chain_start_sha` to null and `captain` in one
  write.
- **Step 4, Captain.** After the verdict: increment `review_cycles`, store the
  verdict and findings in `captain_findings`, and set `verify`, in one write.
- **Step 5, BlackWidow.** After her verification: PASS (or a user-accepted
  CONDITIONAL PASS at the cycle limit) → step 7 close-out, then `closed` in the
  same write as the close-out's end. FAIL or CONDITIONAL PASS under the limit →
  step 6: append the verified findings as unchecked `[Review][Patch]` bullets
  (skipping any already present, so a repeat is harmless), set the
  `sprint-status.yaml` entry to `in-progress`, then `fixing` and step 3.
- **Step 8, epic done + retrospective offer.** Runs once epic N is complete: every
  story key for epic N (keys starting `N-`, excluding `epic-N` and
  `epic-N-retrospective`; at least one) is `done`. The main loop first sets `epic-N: done` and
  `last_updated` (skip if already `done`); the `bmad-sprint-planning`
  sprint-status header marks `in-progress → done` as manual, so the relay owns
  it. The relay never downgrades `epic-N`; only the user reopens it (Phase 7's
  `done` → stop and ask). Neither write has a marker: the epic status lives in
  `epic-N`, and `bmad-retrospective` records its run in the
  `epic-N-retrospective` entry of `sprint-status.yaml`. After the `epic-N`
  write, if the retrospective is owed (below), make the retrospective offer;
  the relay never runs `bmad-retrospective` without it. The definitions below
  are canonical; other files point here.
  - **In this sequence.** An epic is in this sequence when at least one of its
    story keys is in `loop_state.completed`, has a non-null
    `loop_state.stories[<key>].baseline_commit` (`NO_VCS` counts), or has
    `review_cycles >= 1`. Marker inference never writes any of these fields,
    so stories built by an earlier sequence do not pull their epic in.
    **Legacy fallback:** if the state file has no `track`, or no
    `loop_state.completed` entry matches a `development_status` key, every
    complete epic is in this sequence.
  - **Owed.** A retrospective is owed for epic N when the epic is complete
    (as defined above), it is in this sequence, its `epic-N-retrospective`
    entry exists and is not `done`, and `"N"` is not in
    `loop_state.retros_declined`. A missing `epic-N-retrospective` key means
    not owed.
  - **Retrospective offer.** Ask: "[1] Run retrospective for epic N / [2] Skip",
    naming any existing `{implementation_artifacts}/epic-N-retro-*.md` (a crash
    between the doc save and the status write leaves the doc with the entry not
    `done`; the user then skips rather than writing a duplicate). [1] → run
    `bmad-retrospective` in the main loop with epic N passed explicitly (its
    auto-detection picks the highest epic with any `done` story) and relay its
    output. [2] → append `"N"` (a string) to `loop_state.retros_declined` and
    save the state file immediately. A [1] the user abandons leaves the entry
    not `done` and no decline recorded, so the epic is offered again.
    `bmad-retrospective` has no skip of its own and writes `done` only after
    its doc is saved, which is why the decline is recorded here.
  - **Epic close-out sweep.** After the story loop, before advancing to Phase 9
    (fresh entry or resume), in this order: (1) the epic sweep: set
    `epic-N: done` as above (with `last_updated`, preserving comments and
    structure) for every complete epic (as defined above, at least one story
    key) whose `epic-N` entry is not `done`, and tell the user which epics the
    sweep set to `done` (none → say nothing); (2) the retrospective offer for
    each owed epic, in epic order. On a fresh entry this covers epics whose
    stories were already `done` (inferred `closed`), which step 8 never
    reached in the story loop.
  - **Exit.** Phase 8 is finished when every story is `closed` and every
    complete epic in this sequence has had its retrospective run or declined.

## Execution Model — wrap, don't reimplement

Each phase **invokes its real `bmad-*` skill** (main loop, then a read-only owner
verifies where one is mapped). In Phase 7 the main loop runs `bmad-create-story`
and **dispatches Thor** to run `bmad-dev-story` (after `bmad-testarch-atdd` on
the full track), relaying his Blocked reports
(`§3.12`). There are no persona overlays to load and no self-contained
phase logic — the wrapped skill carries the authoring instructions. The
`references/bmad/phase-{N}-*.md` and `track-quick.md` files are thin stubs
documenting the mapping (skill + owner + mode) plus the wrapped skill's completion
criteria, for quick lookup at phase entry.
