#!/usr/bin/env python3
"""
parse-debug-log.py - Parse a Claude Code debug log for skill testing verdicts.

Extracts:
- Bash tool errors
- Permission prompts
- Write/Edit failures
- Skill invocations
- Agent dispatches
- Files written

Exit codes:
  0 = parsed successfully (issues may still exist in the log)
  1 = error reading log file
"""
import argparse
import json
import re
import sys
from pathlib import Path


def parse_log(log_path: Path) -> dict:
    try:
        content = log_path.read_text(errors="replace")
    except Exception as e:
        print(f"ERROR: Cannot read log file: {e}", file=sys.stderr)
        sys.exit(1)

    lines = content.splitlines()

    result = {
        "log_file": str(log_path),
        "bash_errors": [],
        "permission_prompts": [],
        "write_failures": [],
        "skill_invocations": [],
        "agents_dispatched": [],
        "files_written": [],
    }

    for i, line in enumerate(lines):
        # Bash tool errors
        if "Bash tool error" in line or "bash: command not found" in line:
            result["bash_errors"].append(line.strip())

        # Permission prompts
        if "permission" in line.lower() and ("prompt" in line.lower() or "allow" in line.lower()):
            result["permission_prompts"].append(line.strip())

        # Write/Edit failures
        if ("Write tool" in line or "Edit tool" in line) and (
            "error" in line.lower() or "failed" in line.lower() or "fail" in line.lower()
        ):
            result["write_failures"].append(line.strip())

        # Skill invocations (looking for /skill-name patterns)
        skill_match = re.search(r'/(avengers-\w+|bmad|debug-session|enable-ironman|disable-ironman|git-workflow|equip-\w+)\b', line)
        if skill_match:
            skill_name = skill_match.group(1)
            if skill_name not in result["skill_invocations"]:
                result["skill_invocations"].append(skill_name)

        # Agent dispatches
        if "Agent(" in line or "agent_dispatch" in line.lower():
            agent_match = re.search(r'Agent\((\w+)\)', line)
            if agent_match:
                agent_name = agent_match.group(1)
                if agent_name not in result["agents_dispatched"]:
                    result["agents_dispatched"].append(agent_name)

        # Files written (Write tool calls)
        write_match = re.search(r'Write\s+(?:tool\s+)?(?:to\s+)?["\']?([^\s"\']+\.[a-zA-Z]+)["\']?', line)
        if write_match:
            fname = write_match.group(1)
            if fname not in result["files_written"]:
                result["files_written"].append(fname)

    return result


def main():
    parser = argparse.ArgumentParser(description="Parse Claude Code debug log")
    parser.add_argument("--log-file", type=Path, required=True, help="Path to debug log")
    args = parser.parse_args()

    if not args.log_file.exists():
        print(f"ERROR: Log file not found: {args.log_file}", file=sys.stderr)
        sys.exit(1)

    result = parse_log(args.log_file)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
