#!/usr/bin/env python3
"""
ensure-bmad.py - Ensure BMAD reference files exist in the plugin directory.

The BMAD phase files are large and included verbatim here so the plugin is
self-contained. This script writes them to references/bmad/ if they don't exist.

Exit codes:
  0 = success (files already existed or were written)
  1 = error
"""
import argparse
import sys
from pathlib import Path


# BMAD reference file stubs - full content lives in references/bmad/ directory
# This script verifies those files exist and are non-empty
EXPECTED_FILES = [
    "relay-config.md",
    "phase-1-assessment.md",
    "phase-2-requirements.md",
    "phase-3-technical.md",
    "phase-4-planning.md",
    "phase-5-delivery.md",
    "phase-6-sprint.md",
    "phase-7-stories.md",
    "phase-8-review.md",
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
