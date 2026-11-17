# Paired reviewers: enforce the recipient, tie the ship gate to the reviewed commit

## Objective
The paired-reviewer protocol (a Thor and its own Captain running the
build-review-fix loop with `SendMessage`) was enforced only by documentation and a
text check. Harden it: enforce the message recipient at runtime, treat findings as
claims rather than commands, tie the ship gate to the reviewed sha, keep the Fleet
rules from disturbing a pair mid-loop, state the dispatch mechanism and its
fallback, exclude the `/bmad` and `/sdd` relays, and reconcile the persona's
Quality Gate and Closure Loop with the paired loop.

## Scope

**Files to Create/Modify**
- `scripts/pair-registry.py` — the project-local pair registry (`.avengers/pairs.json`: `register`, `unregister`, `list`) and the `guard` decision
- `scripts/sendmessage-guard.sh` — PreToolUse hook entry; turns every outcome but an explicit allow into exit 2
- `hooks/hooks.json` — `PreToolUse` hook on `SendMessage`
- `.claude/rules/ironman-delegation.md` — Paired Reviewers rewritten (dispatch order and registry, verdict copy with range and finding list, ship gate tied to the sha, claims not commands, guard and forbidden targets, pair messages as agent output, resume-by-message fallback, relay exclusion); Keep the Fleet Busy item 8; Exceptions item 6 (registry calls)
- `agents/thor.md`, `agents/captain.md` — When Paired updated to match
- `personas/ironman.md` — pairing pointer, Fleet exemption, Quality Gate and Closure Loop reconciled
- `scripts/compact-resume.sh` — the Fleet exemption in the post-compaction reminder
- `tests/test_sendmessage_guard.py` — hook unit tests
- `tests/test_doc_consistency.py` — tightened messaging checker
- `README.md`, `TESTING.md`, `.github/workflows/tests.yml` — hook docs, test docs, byte-compile `scripts`

## Design & Structure
- **Guard.** `sendmessage-guard.sh` runs `pair-registry.py guard`, which reads the hook payload on stdin. It restricts subagents only, keyed on the documented `agent_id` field of the PreToolUse input (`agent_type` alone is not used: `claude --agent <name>` sets it on a main session).
  - No `agent_id`: a main-session call; allowed, any target, so the orchestrator is never cut off.
  - `agent_id` present: a target with whitespace or `[` is denied first. A sender registered in a pair may message `main` and its own partner's agentId; any other subagent only `main`. Another team's agents are denied. Denials exit 2 with the reason on stderr.
- **Fail closed (subagents).** A missing, unreadable or malformed registry, an unset `CLAUDE_PROJECT_DIR`, or a malformed `agent_id` leaves only `main`. A payload that is not a JSON object cannot be attributed to the main session and is denied. Claude Code treats any exit other than 0 and 2 as non-blocking, so the shell entry maps a crash or a missing `python3` to exit 2 (main session included).
- **Debug.** `AVENGERS_PAIR_GUARD_LOG=<file>` appends one JSON line per guarded call with the payload's keys only (plus `agent_type`).
- **Registry.** `{"version": 1, "pairs": {"<team>": {"thor": "<id>", "captain": "<id>"}}}`, written atomically; `register` and `unregister` hold an exclusive `flock` on `.avengers/pairs.lock` around the read-modify-write. An agentId belongs to one team. IronMan dispatches both agents with `run_in_background`, registers each id immediately after its spawn returns, passes `--project-dir` from the in-scope `Avengers project dir:` session line, and unregisters the team when the loop ends. Thor may retry a round-1 "no registered partner" denial once.

## Mechanism and open item
- **Relied on:** resume-by-message. Each side ends its run after sending, and the partner's message resumes it. This supersedes, for paired builder teams only, the "no SendMessage path" note in `agent-escalation-path.md`.
- **Open item:** verify resume-by-message end to end (a finished subagent resumed by a `SendMessage` from its partner, and from `main`) on the Claude Code versions the plugin supports.
- **Open item:** confirm empirically, once, with `AVENGERS_PAIR_GUARD_LOG`, that main-session SendMessage calls carry no `agent_id` and that subagent calls carry it. The hooks docs state the latter; the former is implied, not stated.
- **Open item:** the registry is writable by agents with Write or Bash, and an agentId is any single word, so the guard stops misdirected or injected targets, not a deliberately hostile agent.
- **Open item:** the `agent_id` in the hook input equals the agentId the Agent tool returns at spawn (the id IronMan registers). Unverified; if they differ, every paired send is denied and the fallback takes over.
- **Open item:** a missing hook script cannot fail closed (`bash` exits 127, non-blocking).
- **Fallback:** if a Captain run ends with no verdict copy to `main` for the round, or a partner never resumes, IronMan unregisters the pair and runs the review loop by re-dispatch, as for an unpaired team.

## Acceptance Criteria
- [ ] A main-session call (no `agent_id`, including an `agent_type`-only `--agent` session) is allowed to any target
- [ ] A registered subagent may message `main` and its own partner, not another team's agents; an unregistered subagent only `main`; a session name and `name [ref]` are denied
- [ ] For subagents, no registry or a malformed payload carrying `agent_id` leaves only `main`; a guard that cannot run denies
- [ ] Paired sections are allowed only in the three protocol files and not inside code fences
- [ ] A messaging verb in a paired section must be followed by an allowed recipient
- [ ] Every agent has a frontmatter `tools:` line; the `tools:` skip applies to frontmatter only
- [ ] `python3 -m unittest discover -s tests` passes

## Status
- [ ] Spec approved by user (written from the operator's brief for this follow-up)
