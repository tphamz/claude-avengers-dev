#!/bin/bash
# Avengers Dev - PreToolUse guard for SendMessage (paired reviewers).
#
# Restricts subagents only (payloads carrying `agent_id`): a paired agent may
# message IronMan (`main`) and its own partner registered in
# <project>/.avengers/pairs.json; any other subagent only `main`. Main-session
# calls are not restricted. The decision is made by `pair-registry.py guard`,
# which reads the hook payload on stdin; see that file for the rules.
#
# FAILS CLOSED. Claude Code blocks a tool call only on exit 2; any other non-zero
# exit is a non-blocking error and the call would go through. So every outcome
# other than an explicit allow (exit 0) becomes exit 2 here: a deny, a crash, a
# missing python3 or a missing pair-registry.py all deny the call. Without a
# working guard the sender cannot be told apart, so this denies main-session
# calls too. The one gap: if THIS script is missing, bash exits 127 before any
# of it runs, and Claude Code lets the call through.

_guard="$(dirname "${BASH_SOURCE[0]}")/pair-registry.py"
python3 "$_guard" guard
_status=$?
if [ "$_status" -eq 0 ]; then
  exit 0
fi
if [ "$_status" -ne 2 ]; then
  echo "SendMessage denied: the pair guard could not run (exit $_status), so the call fails closed." >&2
fi
exit 2
