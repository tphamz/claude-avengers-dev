#!/usr/bin/env python3
"""
ensure-bmad.py - Verify the BMAD reference files ship with the plugin.

The BMAD relay reads thin reference stubs (relay config, per-phase stubs, and the
quick-track stub) from references/bmad/. This script checks that every expected
file exists and is non-empty. It does not write anything; missing files are
reported as a warning on stderr.

Exit codes:
  0 = success (all files present, or missing files warned about)
  1 = error (references/bmad/ directory not found)
"""
import argparse
import sys
from pathlib import Path


# BMAD reference stubs expected in references/bmad/ (13 files)
EXPECTED_FILES = [
    "relay-config.md",
    "phase-0-kb.md",
    "phase-1-assessment.md",
    "phase-2-requirements.md",
    "phase-3-technical.md",
    "phase-4-planning.md",
    "phase-4.5-hardening.md",
    "phase-5-delivery.md",
    "phase-6-sprint.md",
    "phase-7-stories.md",
    "phase-8-review.md",
    "phase-9-kb-refresh.md",
    "track-quick.md",
]


def main():
    parser = argparse.ArgumentParser(description="Ensure BMAD reference files exist")
    parser.add_argument("--plugin-dir", type=Path, required=True, help="Plugin root directory")
    args = parser.parse_args()

    plugin_dir = args.plugin_dir.resolve()
    bmad_dir = plugin_dir / "references" / "bmad"

    if not bmad_dir.exists():
        print(f"ERROR: BMAD directory not found: {bmad_dir}", file=sys.stderr)
        print(f"Expected the plugin to be fully installed at: {plugin_dir}", file=sys.stderr)
        sys.exit(1)

    missing = []
    for fname in EXPECTED_FILES:
        fpath = bmad_dir / fname
        if not fpath.exists():
            missing.append(fname)
        elif fpath.stat().st_size == 0:
            missing.append(f"{fname} (empty)")

    if missing:
        print(f"WARNING: Missing BMAD reference files:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print(f"These files should be present in {bmad_dir}", file=sys.stderr)
        # Non-fatal: continue
    else:
        print(f"BMAD reference files verified ({len(EXPECTED_FILES)} files OK)")

    sys.exit(0)


if __name__ == "__main__":
    main()
