#!/bin/bash
# Avengers Dev - session start banner + persona injection

# Scope guard: resolve this session's workspace scope exactly once. The resolver
# is shared with compact-resume.sh (scripts/lib/avengers-scope.sh) so the two
# hooks can never drift. With no scope configured it answers `yes` everywhere.
# If the lib cannot be loaded the scope is `unknown`, and each guard below
# applies its own fail direction.
AVENGERS_SCOPE=unknown
_scope_lib="$(dirname "${BASH_SOURCE[0]}")/lib/avengers-scope.sh"
if [ -r "$_scope_lib" ]; then
  # shellcheck source=lib/avengers-scope.sh
  . "$_scope_lib" && AVENGERS_SCOPE="$(avengers_scope_state)"
fi
unset _scope_lib
# A truncated or half-sourced lib must not produce a fourth state.
case "$AVENGERS_SCOPE" in yes|no|unknown) ;; *) AVENGERS_SCOPE=unknown ;; esac

# Banner: FAILS OPEN - prints on `yes` and on `unknown`. The banner is cosmetic,
# so showing it in a session we could not place costs little, and it carries the
# `unknown` note below; hiding it would make that note disappear with it.
if [ "$AVENGERS_SCOPE" = yes ] || [ "$AVENGERS_SCOPE" = unknown ]; then

cat << 'EOF'

 ⚡ AVENGERS DEV ⚡

    ▄
   ███
  ██ ██
 ███████
██     ██
🟠 IronMan    - orchestrator  Agent(ironman)
⚫ BlackWidow - spy & explorer Agent(avengers-dev:blackwidow)
🟡 Thor       - builder       Agent(avengers-dev:thor)
🔵 Captain    - sentinel      Agent(avengers-dev:captain)
🟢 Hulk       - engineer      Agent(avengers-dev:hulk)
🔴 Vision     - BMAD          /bmad

/avengers-init · /avengers-test · /bmad

"Avengers, assemble!" 🦸‍♂️

EOF

  if [ "$AVENGERS_SCOPE" = unknown ]; then
cat << 'EOF'
⚠️  Workspace scope could not be determined (the project directory, every
    configured scope root, or the scope file failed to resolve). The IronMan
    persona was NOT injected for this session.

EOF
  fi

fi

# Persona injection: FAILS CLOSED - prints only when the scope is definitely
# `yes`. The asymmetry with the banner above is the point: the persona changes
# how the whole session behaves, so injecting it into a session we could not
# place would put it exactly where the user scoped it out. Failing closed is the
# loud failure instead - no in-character greeting, noticed in seconds, fixed in
# seconds.
if [ "$AVENGERS_SCOPE" = yes ]; then
cat << 'EOF'
[Claude: a new session has started. Open your first reply by greeting the operator in character as Tony Stark / Iron Man and briefly introducing the team, then proceed with their request. Stay in character throughout the session - begin replies with a short in-character line, and when you relay an agent's result, lead with that agent's voice.]

EOF
fi

# The session's project directory, for `pair-registry.py --project-dir`: the
# SendMessage guard reads the registry under CLAUDE_PROJECT_DIR, which the Bash
# tool does not see, so IronMan copies this exact value. Printed raw (never
# resolved) because the guard uses the raw value. In scope only, like the persona:
# an out-of-scope session prints nothing but the plugin-root line.
if [ "$AVENGERS_SCOPE" = yes ] && [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  echo "Avengers project dir: $CLAUDE_PROJECT_DIR"
fi

# Absolute plugin root for agent Bash (CLAUDE_PLUGIN_ROOT is empty in subagent Bash).
# DO NOT GUARD OR EARLY-EXIT PAST THIS. IronMan's dispatch protocol reads this
# line for the absolute workstation.py path; it must print in every scope.
PLUGIN_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT:-$(dirname "${BASH_SOURCE[0]}")/..}" 2>/dev/null && pwd -P)"
if [ -n "$PLUGIN_ROOT" ]; then
  echo "Avengers plugin root: $PLUGIN_ROOT"
  echo
fi
