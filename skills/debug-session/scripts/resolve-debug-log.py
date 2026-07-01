#!/usr/bin/env python3
"""
resolve-debug-log.py - Find the most recent Claude Code debug log.

Searches common locations for debug output files.

Exit codes:
  0 = found, prints path to stdout
  1 = not found
"""
import sys
from pathlib import Path


SEARCH_LOCATIONS = [
    # Claude Code default debug output
    Path.home() / ".claude" / "logs",
    Path("/tmp"),
    Path.cwd(),
]

LOG_PATTERNS = [
    "claude-debug-*.log",
    "claude-*.log",
    "debug-*.log",
    "*.debug.log",
]


def find_most_recent_log() -> Path | None:
    candidates: list[Path] = []

    for location in SEARCH_LOCATIONS:
        if not location.exists():
            continue
        for pattern in LOG_PATTERNS:
            candidates.extend(location.glob(pattern))

    if not candidates:
        return None

    # Return most recently modified
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    log = find_most_recent_log()
    if log is None:
        print(
            "No debug log found. Run: claude --debug --plugin-dir /path/to/avengers-dev",
            file=sys.stderr
        )
        sys.exit(1)

    print(str(log))
    sys.exit(0)


if __name__ == "__main__":
    main()
