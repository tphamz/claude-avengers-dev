# SDD Sequence - Spec-Driven Change Scheme

## When to Equip

Use when IronMan says "spec this change", "run /sdd", or "use OpenSpec" for a
feature or change that should be specified before it is built, but does not need a
PRD and architecture. For those, use `bmad-sequence` (or `/sdd <name> full`, which
hands off to it).

This scheme runs `/avengers-dev:sdd`. It drives the OpenSpec CLI through
`skills/sdd/scripts/sdd-openspec.py`; it does not reimplement OpenSpec. OpenSpec
>= 1.13 must be installed separately (`npm i -g @fission-ai/openspec@latest`).

Tracks: `quick` (0 → P lite → B → V → A, `spec-driven` schema), `standard`
(default, `avengers-sdd` schema with a tests artifact), `full` (hands off to
`/bmad`).

## The Crew — phase → tool → owner → tracks

| Phase | Tool / procedure | Owner | Tracks |
| ----- | ---------------- | ----- | ------ |
| 0 Preflight | `sdd-openspec.py preflight` → workstation (`--link openspec`) → `init` → KB check (BMAD only) | main loop | quick, standard |
| E Explore (optional) | `openspec/specs/` and code, with the user | main loop (Vision voice) | standard |
| P Propose | `sdd-openspec.py new` → `instructions` per artifact | main loop (Vision voice) | quick (lite), standard |
| H Harden | `sdd-openspec.py validate` + adversarial / edge-case review (with `_bmad/`: main loop runs `bmad-review-*` skills first) | Captain (`adversarial` lens), verifies read-only | standard |
| R Readiness | readiness of the change | Hulk | standard |
| B Build | failing tests from `tests.md` first (standard), then `tasks.md` | Thor | quick, standard |
| V Verify + review | `references/sdd/verify.md` + code review | Captain | quick, standard |
| A Archive + KB | `sdd-openspec.py archive` → `bmad-kb.py impact` (BMAD only) → md commit | main loop | quick, standard |

**Why the split:** proposing and fixing specs ask the user questions, so they run
in the main loop; hardening, readiness, build and verify belong to a specialist
Avenger and need no user input.

## Design-Implementation Boundary

Standard track only. After R, Hulk reports the readiness verdict and the relay
halts. IronMan presents it for an explicit choice — **[1] Continue into
implementation / [2] Exit** — before B begins. No auto-advance. If readiness is
FAIL or Harden Criticals are unresolved, [1] needs `override` plus a reason.

## Artifacts

The OpenSpec change under `openspec/changes/<id>/` (proposal, delta specs, design,
tests on standard, tasks), merged into the living specs under `openspec/specs/` by
archive. With an md workstation, `openspec/` is a symlink into it. The relay's
state file: `.avengers/relay-sequences/sdd-{name}.yaml`.

## Completion Criteria
- [ ] All phases for the chosen track completed (0 through A)
- [ ] Standard track: hard gate cleared with explicit user authorization (any
      override recorded with a reason)
- [ ] Standard track: failing tests written before the code, then passing
- [ ] Captain verdict: PASS or CONDITIONAL PASS with no `[CRITICAL]` (max 3 review
      cycles, else escalate)
- [ ] Change archived by `sdd-openspec.py archive` (any `--allow-incomplete`
      recorded with a reason); BMAD KB refresh evaluated when `_bmad/` exists
- [ ] State file transitioned to `complete` (or `handed_off` for `full`)
