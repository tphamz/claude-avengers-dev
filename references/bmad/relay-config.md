# BMAD Methodology Relay - Configuration

This is the configuration and protocol reference for the Avengers BMAD relay.
The relay **wraps the real BMAD-METHOD `bmad-*` skills** — it does not reimplement
them. Vision (the conductor) reads this at relay start to understand operational
parameters and the phase→skill+owner map.

## Relay Identity

- **Name:** BMAD — the Avengers relay that conducts the real BMAD-METHOD framework
  (mnemonic: *Build More Architect Dreams*). It orchestrates the installed `bmad-*`
  skills through the crew; it is not a competing methodology.
- **Type:** skill-wrapping methodology-relay
- **Phases:** 8 (design 1-5, implementation 6-8)
- **Conductor:** Vision agent (voice + map, not executor)

## Phase Map — phase → real skill → owner → mode

Every wrapped skill except `bmad-dev-story` runs **in the main loop** (Vision's
voice), so the skill can elicit from the user and write its artifacts; that
includes Phase 7's `bmad-create-story`. In Phases 1a, 5 and 8 the owning Avenger
is then dispatched **read-only to verify** the result. In Phase 7 Thor runs
`bmad-dev-story` to build, and the main loop relays each of its HALTs to the user
(`§3.8`).

| Phase | Real skill(s) | Owner | Mode |
|-------|---------------|-------|------|
| 1a Discovery | `bmad-document-project` / `bmad-investigate` | main loop; `Agent(avengers-dev:blackwidow)` verifies | interactive + verify |
| 1b Brief | `bmad-product-brief` | main loop (Vision voice) | interactive |
| 2 PRD | `bmad-prd` | main loop (Vision voice) | interactive |
| 3 Architecture | `bmad-create-architecture` | main loop (Vision voice) | interactive |
| 4 Epics/Stories | `bmad-create-epics-and-stories` | main loop (Vision voice) | interactive |
| 5 Readiness | `bmad-check-implementation-readiness` | main loop; `Agent(avengers-dev:hulk)` verifies | interactive + verify |
| — | **DESIGN-IMPLEMENTATION BOUNDARY** | IronMan | **hard gate** |
| 6 Sprint plan | `bmad-sprint-planning` | main loop (Vision voice) | light |
| 7 Build (per story) | `bmad-create-story` → `bmad-dev-story` | main loop runs `bmad-create-story`; `Agent(avengers-dev:thor)` runs `bmad-dev-story` per story | interactive + build (HALTs relayed) |
| 8 Review | `bmad-code-review` + `bmad-retrospective` | main loop; Thor fixes, `Agent(avengers-dev:captain)` reviews, `Agent(avengers-dev:blackwidow)` verifies, main loop closes out | interactive + verify |

**Why the split:** the wrapped `bmad-*` skills halt for user input and write
artifacts step by step; `bmad-code-review` also spawns its own subagents. A
subagent runs blind and cannot elicit, and BlackWidow, Hulk and Captain have no
Write, Edit or Agent tools. So the skills run in the main loop and those owners
verify the output read-only. `bmad-dev-story` changes source code, so it runs in
Thor, who returns a Blocked report whenever it stops for a human. The main loop
may read broadly and write BMAD artifacts while running a wrapped skill and in the
relay steps around it (the Phase 7 epic-status write, Blocked resets, Phase 8
reconciliation and close-out), but never modifies source code — code changes
(including code-review patches) always go to Thor.

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
current_phase: string         # 1a | 1b | 2 | 3 | 4 | 5 | 6 | 7 | 8
design_implementation_boundary_passed: bool  # Phase 5->6 hard gate
created_at: timestamp
last_active: timestamp

relay_modifiers:
  existing_code_in_scope: bool   # Brownfield mode (drives Phase 1a skill choice)

loop_state:                      # Phases 7 and 8
  total_items: int
  completed: list                # story keys whose Phase 7 build reported done
  in_progress: string | null     # story key of the dispatch that last started (§3.8 step 2)
  remaining: list
  phase8_start_sha: string       # HEAD at Phase 8 entry, written once (or NO_VCS)
  stories:                       # per story key (story file name without .md)
    <story_key>:
      baseline_commit: string    # Phase 7 chain start: pre_sha of the first dev-story dispatch,
                                 # written before that dispatch, never overwritten (or NO_VCS)
      phase7_end_sha: string     # post_sha of the Phase 7 dispatch that reported done,
                                 # never overwritten (or NO_VCS)
      chain_start_sha: string | null  # Phase 8 fix chain start: pre_sha of the chain's first
                                 # dispatch, written before it; null once the fix range is recorded
      phase8_fix_ranges: list    # one <chain_start_sha>..<done post_sha> per Phase 8 fix (or NO_VCS)
      review_cycles: int         # Captain verdicts so far in Phase 8 (max 3, §2.10)
      blocked:                   # set while Thor's last report was Blocked (§3.8), else null
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

**Legacy state files:** an older `phase8_fix_shas` list (one commit SHA per fix)
is read as the ranges `<sha>^..<sha>` and written back as `phase8_fix_ranges`.

Artifact paths are owned by the wrapped `bmad-*` skills and resolved from
`_bmad/bmm/config.yaml` (see `§2.8`) — the relay does not dictate them.

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
auto-advances or auto-blocks the gate.

### §2.8 Artifact Path Resolution

Before dispatching a verifying Avenger, the main loop reads
`_bmad/bmm/config.yaml`, substitutes `{project-root}`, and passes **concrete file
paths** — never globs or unresolved `{placeholders}`. Keys and installer defaults:

| Key | Default | Written there |
|-----|---------|---------------|
| `project_knowledge` | `docs` | `bmad-document-project` output |
| `planning_artifacts` | `_bmad-output/planning-artifacts` | `implementation-readiness-report-{date}.md` (pass the newest file) |
| `implementation_artifacts` | `_bmad-output/implementation-artifacts` | story files, `sprint-status.yaml`, `deferred-work.md`, `investigations/{slug}-investigation.md`, `epic-{N}-retro-{date}.md` |

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
  Phase 8 fix) may take several dispatches: Blocked re-dispatches (`§3.8`),
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
  3. Uncommitted story work. Run `git status --porcelain --untracked-files=all`
     and flag only the paths that also appear in the story's File List or in
     Thor's reported Files Changed or Work state. Every other path is ignored,
     including the relay state file `.avengers/relay-sequences/*`, anything
     under `{planning_artifacts}` or `{implementation_artifacts}`, and an
     untracked `_bmad/`. A flagged path is work the range would miss: tell the
     user and dispatch Thor to commit exactly those paths. That dispatch is part
     of the same chain (it keeps the chain start). After its report, take
     `post_sha` again; it replaces the earlier `post_sha` as the chain's end.
     Rerun the checks on it and record it. If check 3 still flags, stop and ask
     the user.
  4. `git log --oneline <chain start>..<post_sha>` does not match the commit(s)
     Thor reported → flag the mismatch to the user.
- **Unborn HEAD.** In a git repository with no commits yet, `git rev-parse HEAD`
  fails; use the empty-tree hash `4b825dc642cb6eb9a060e54bf8d69288fbee4904` for
  that `pre_sha` or `post_sha`. **This is the one rule for an empty-tree left
  side**, used by every range consumer (Phase 8 code review, Captain,
  BlackWidow, the checks above, the resume fallback). When a range's left side
  is the empty-tree hash:
  - diff it with `git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904 <sha>`;
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

On a resume into Phase 7 or 8, in this order:

1. **Suspended Blocked stories first.** If any `loop_state.stories` entry has a
   `blocked` entry, replay it to the user before any dispatch: the stored
   `halt_point`, `question`, `options` and `work_state`. Ask one plain question:
   answer, or keep it suspended. Keep suspended → leave `status: suspended` and
   stop. Answer → continue at `§3.8` step 4's answer path: add the `[Gate]`
   subtask and do the status reset where they apply, clear `blocked`, and
   re-dispatch Thor with the answer, the stored `work_state` and the stored
   `resume_instruction`. The chain start is the recorded `baseline_commit`
   (Phase 7) or `chain_start_sha` (Phase 8), never a new `pre_sha`.
2. **Then the loop.** Continue the `§3.8` per-story loop, which skips finished
   stories. In Phase 8, keep the recorded `phase8_start_sha`, and rebuild any
   missing story ranges with the `§2.9` resume fallback.

### §3.5 Phase Boundary Confirmation

Each interactive phase announces completion and waits for user confirmation before
advancing. Format: "Phase N ({name}) complete. {summary}. Ready for Phase N+1?"
Phases with a verifying Avenger (1a, 5, 8) and the Phase 7 build report through
that Avenger; IronMan relays, then advances. A Thor Blocked report is relayed as a
question to the user (`§3.8`), never advanced past.

### §3.6 Design-Implementation Boundary (Hard Gate)

The boundary between Phase 5 and Phase 6 is a hard gate. User must explicitly choose:
- [1] Continue into implementation
- [2] Exit (artifacts saved, relay suspended)

No auto-advance. No batch-through. Set `design_implementation_boundary_passed: true`
only on [1].

### §3.7 Scope Creep Prevention

During Phase 7, if implementation surfaces out-of-scope requirements:
- Surface to user with three options (note/defer, pause-replan, add-informally)
- Do not implement out-of-scope items silently

### §3.8 Phase 7 Per-Story Sequence and Blocked Relay

For each story, in `development_status` order in `sprint-status.yaml`. **Skip
a story** whose `development_status` entry is `review` or `done`, or whose key is
in `loop_state.completed`, unless it has a `blocked` entry (a suspended Blocked
story; `§3.2` step 1 handles it before the loop). So a resume never re-runs a
finished story.

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
   `loop_state` yet, write this `pre_sha` as its `baseline_commit` and save the
   state file **before** dispatching. Never overwrite an existing
   `baseline_commit`.
3. **Build (Thor).** Dispatch `Agent(avengers-dev:thor)` to run
   `bmad-dev-story` on the explicit story file path, with this instruction: at
   any dev-story HALT or ask point, do not guess and do not work around it — stop
   without committing and return a Blocked report (`agents/thor.md`). dev-story's
   step-10 completion explanation and next-step prompts are not stops: finish,
   run tests, commit, and report done.
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
5. **Done.** Record `post_sha` and run the `§2.9` checks on
   `<baseline_commit>..<post_sha>` (check 3 may add a commit dispatch to the same
   chain and a new `post_sha`). Cross-check `baseline_commit` against the story
   frontmatter, then write `phase7_end_sha` (the final `post_sha`) to
   `loop_state.stories[<story_key>]` unless one is already recorded. Add the key
   to `completed`, set `in_progress` to null, and update `remaining`.

Phase 8 step 3 (Thor resolving `[Review][Patch]` items) uses the same Blocked
handling (steps 4-5 here): the stored `blocked` fields, the relay, the `[Gate]`
subtask for regression or definition-of-done HALTs, the status reset, and
re-dispatches that carry the answer, Work state and Resume instruction. Its chain
start is `chain_start_sha`, written before the chain's first dispatch, and its
fix range `<chain_start_sha>..<done post_sha>` spans the whole chain. Blocked
re-dispatches never count toward `review_cycles`.

## Execution Model — wrap, don't reimplement

Each phase **invokes its real `bmad-*` skill** (main loop, then a read-only owner
verifies where one is mapped). In Phase 7 the main loop runs `bmad-create-story`
and **dispatches Thor** to run `bmad-dev-story`, relaying his Blocked reports
(`§3.8`). There are no persona overlays to load and no self-contained
phase logic — the wrapped skill carries the authoring instructions. The
`references/bmad/phase-{N}-*.md` files are thin stubs documenting the mapping
(skill + owner + mode) plus the wrapped skill's completion criteria, for quick
lookup at phase entry.
