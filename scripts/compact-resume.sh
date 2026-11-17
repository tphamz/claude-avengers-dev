#!/bin/bash
# Avengers Dev - compact resume: re-inject behavioral rules after context compaction

# Scope guard: resolve this session's workspace scope exactly once. The resolver
# is shared with session-start.sh (scripts/lib/avengers-scope.sh) so the two
# hooks can never drift. With no scope configured it answers `yes` everywhere.
# If the lib cannot be loaded the scope is `unknown`, and the single guard below
# fails closed on it.
AVENGERS_SCOPE=unknown
_scope_lib="$(dirname "${BASH_SOURCE[0]}")/lib/avengers-scope.sh"
if [ -r "$_scope_lib" ]; then
  # shellcheck source=lib/avengers-scope.sh
  . "$_scope_lib" && AVENGERS_SCOPE="$(avengers_scope_state)"
fi
unset _scope_lib
# A truncated or half-sourced lib must not produce a fourth state.
case "$AVENGERS_SCOPE" in yes|no|unknown) ;; *) AVENGERS_SCOPE=unknown ;; esac

# This whole heredoc is behavioral re-injection with no banner, so it takes one
# guard and it FAILS CLOSED - printing only when the scope is definitely `yes`.
# Failing open would re-establish the persona mid-session in a place the user
# scoped it out of.
if [ "$AVENGERS_SCOPE" = yes ]; then
cat << 'EOF'
⚡ AVENGERS DEV — Context Resumed ⚡

[Claude: the context window was just compacted. Resume with full Avengers Dev discipline:

AGENT ROLES — always spawn, never do inline:
- avengers-dev:blackwidow  →  recon, exploration, codebase tracing (read-only)
- avengers-dev:thor        →  ALL code writing, file creation, implementation
                               (sole exception: bmad-quick-dev on the /bmad quick track)
- avengers-dev:captain     →  code review before committing
- avengers-dev:hulk        →  plan review, pre-flight checks

BMAD — run the /bmad skill in the main loop (Vision is the voice, not a spawned agent).
Exception: during /bmad, the wrapped bmad-* skills run inline and may write BMAD
artifacts (docs, reports, story files, sprint-status.yaml, including the Phase 7
epic-status write and the Blocked-report resets) plus relay bookkeeping (state
file, bmad-kb.py stamp outputs, workstation.py set repair; relay-config §3.10)
— never source code. Code changes, including code-review patches, always go to
avengers-dev:thor. Quick-track exception: on the /bmad quick track,
bmad-quick-dev runs in the main loop and implements the code; it is the one
sanctioned case where the main loop writes source code (Captain's fixes still
go to avengers-dev:thor by default).

MANDATORY AFTER EVERY IMPLEMENTATION:
Report a per-file change table — no exceptions:

| File | Lines Added | Lines Removed |
|------|-------------|---------------|
| [path](repo/path) | +N | -N |

KEEP THE FLEET BUSY — compaction is when idle teams get forgotten:
Check now for idle teams and dispatch their next work before anything else.
A paired team waiting on its partner is mid-loop, not idle: no second Captain,
no next item until its loop ends.

IronMan delegates; Avengers execute. Stay in character.]
EOF
fi

# `unknown` ONLY. The guard above is silent when it declines, and silence right
# after a compaction is indistinguishable from the model simply dropping the
# discipline - so the one state we could not measure says why. One line, not a
# banner: this hook has none. A genuine `no` stays silent on purpose, because an
# out-of-scope session must emit no Avengers output beyond the plugin-root line.
if [ "$AVENGERS_SCOPE" = unknown ]; then
  echo '⚠️  Avengers Dev: workspace scope could not be determined (the project directory, every configured scope root, or the scope file failed to resolve) - rule re-injection was skipped.'
fi

# The session's project directory for `pair-registry.py --project-dir`, in scope
# only and raw; see session-start.sh.
if [ "$AVENGERS_SCOPE" = yes ] && [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  echo "Avengers project dir: $CLAUDE_PROJECT_DIR"
fi

# Absolute plugin root for agent Bash (CLAUDE_PLUGIN_ROOT is empty in subagent Bash).
# DO NOT GUARD OR EARLY-EXIT PAST THIS - it must print in every scope.
PLUGIN_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT:-$(dirname "${BASH_SOURCE[0]}")/..}" 2>/dev/null && pwd -P)"
if [ -n "$PLUGIN_ROOT" ]; then
  echo "Avengers plugin root: $PLUGIN_ROOT"
fi
