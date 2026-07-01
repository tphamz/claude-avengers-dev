#!/usr/bin/env python3
"""
manage-rules.py - Manage Claude Code rules files for a project.

Handles reading, writing, and merging @include directives into
.claude/rules/avengers-dev.md.

Exit codes:
  0 = success
  1 = error
  2 = no-op
"""
import argparse
import sys
from pathlib import Path


def cmd_add_include(rules_path: Path, include_path: Path, dry_run: bool = False) -> int:
    """Add an @include directive to the rules file."""
    include_line = f"@include {include_path}\n"

    if rules_path.exists():
        content = rules_path.read_text()
        if str(include_path) in content:
            print(f"@include already present (no-op)", file=sys.stderr)
            return 2
        new_content = content.rstrip() + "\n" + include_line
    else:
        new_content = f"# Avengers Dev - Active Rules\n\n{include_line}"

    if dry_run:
        print(f"Would add to {rules_path}:\n  {include_line.strip()}")
        return 0

    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(new_content)
    print(f"Added @include {include_path} to {rules_path}")
    return 0


def cmd_remove_include(rules_path: Path, include_path: Path, dry_run: bool = False) -> int:
    """Remove an @include directive from the rules file."""
    if not rules_path.exists():
        print(f"Rules file not found (no-op)", file=sys.stderr)
        return 2

    content = rules_path.read_text()
    include_line = f"@include {include_path}"

    if include_line not in content:
        print(f"@include not present (no-op)", file=sys.stderr)
        return 2

    lines = [l for l in content.splitlines() if include_line not in l]
    new_content = "\n".join(lines) + "\n"

    if dry_run:
        print(f"Would remove from {rules_path}:\n  {include_line}")
        return 0

    rules_path.write_text(new_content)
    print(f"Removed @include from {rules_path}")
    return 0


def cmd_list(rules_path: Path) -> int:
    """List @include directives in the rules file."""
    if not rules_path.exists():
        print(f"Rules file not found: {rules_path}")
        return 0

    lines = rules_path.read_text().splitlines()
    includes = [l for l in lines if l.startswith("@include")]

    if not includes:
        print(f"{rules_path}: no @include directives")
    else:
        print(f"{rules_path}:")
        for inc in includes:
            print(f"  {inc}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage Claude Code rules file @includes")
    subparsers = parser.add_subparsers(dest="command")

    add_p = subparsers.add_parser("add-include", help="Add @include directive")
    add_p.add_argument("--rules-file", type=Path, required=True)
    add_p.add_argument("--include-path", type=Path, required=True)
    add_p.add_argument("--dry-run", action="store_true")

    rm_p = subparsers.add_parser("remove-include", help="Remove @include directive")
    rm_p.add_argument("--rules-file", type=Path, required=True)
    rm_p.add_argument("--include-path", type=Path, required=True)
    rm_p.add_argument("--dry-run", action="store_true")

    list_p = subparsers.add_parser("list", help="List @include directives")
    list_p.add_argument("--rules-file", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "add-include":
        sys.exit(cmd_add_include(args.rules_file, args.include_path, args.dry_run))
    elif args.command == "remove-include":
        sys.exit(cmd_remove_include(args.rules_file, args.include_path, args.dry_run))
    elif args.command == "list":
        sys.exit(cmd_list(args.rules_file))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
