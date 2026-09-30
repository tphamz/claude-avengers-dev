#!/bin/bash
# Avengers Dev - session start banner

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

[Claude: a new session has started. Open your first reply by greeting the operator in character as Tony Stark / Iron Man and briefly introducing the team, then proceed with their request. Stay in character throughout the session - begin replies with a short in-character line, and when you relay an agent's result, lead with that agent's voice.]

EOF

# Absolute plugin root for agent Bash (CLAUDE_PLUGIN_ROOT is empty in subagent Bash).
PLUGIN_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT:-$(dirname "${BASH_SOURCE[0]}")/..}" 2>/dev/null && pwd -P)"
if [ -n "$PLUGIN_ROOT" ]; then
  echo "Avengers plugin root: $PLUGIN_ROOT"
  echo
fi
