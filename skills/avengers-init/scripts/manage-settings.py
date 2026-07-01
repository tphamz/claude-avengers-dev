#!/usr/bin/env python3
"""
manage-settings.py - Manage .claude/settings.local.json for a project.

Adds or removes keys from settings.local.json without clobbering existing content.
Supports --dry-run: prints the resulting JSON to stdout without writing.

Exit codes:
  0 = success (or dry-run complete)
  1 = error
  2 = no-op (key already set to that value)
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def load_settings(path: Path) -> dict:
    """Load settings JSON, returning empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"WARNING: Malformed JSON in {path}, backing up and starting fresh: {e}", file=sys.stderr)
        shutil.copy2(path, path.with_suffix(".json.bak"))
        return {}


def cmd_set(settings_path: Path, key: str, value: str, dry_run: bool) -> int:
    """Set a key in settings.local.json."""
    # Parse value as JSON if possible, otherwise treat as string
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    settings = load_settings(settings_path)

    # Check no-op
    if settings.get(key) == parsed_value:
        print(f"Key '{key}' already set to desired value (no-op)", file=sys.stderr)
        return 2

    settings[key] = parsed_value
    output = json.dumps(settings, indent=2)

    if dry_run:
        print(output)
        return 0

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(output)
    print(f"Set '{key}' in {settings_path}")
    return 0


def cmd_remove(settings_path: Path, key: str, dry_run: bool) -> int:
    """Remove a key from settings.local.json."""
    settings = load_settings(settings_path)

    if key not in settings:
        print(f"Key '{key}' not present (no-op)", file=sys.stderr)
        return 2

    del settings[key]
    output = json.dumps(settings, indent=2)

    if dry_run:
        print(output)
        return 0

    settings_path.write_text(output)
    print(f"Removed '{key}' from {settings_path}")
    return 0


def cmd_merge(settings_path: Path, merge_json: str, dry_run: bool) -> int:
    """Merge a JSON object into settings.local.json."""
    try:
        to_merge = json.loads(merge_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON to merge: {e}", file=sys.stderr)
        return 1

    settings = load_settings(settings_path)
    settings.update(to_merge)
    output = json.dumps(settings, indent=2)

    if dry_run:
        print(output)
        return 0

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(output)
    print(f"Merged {len(to_merge)} key(s) into {settings_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage .claude/settings.local.json")
    parser.add_argument("--settings-file", type=Path,
                        default=Path(".claude/settings.local.json"),
                        help="Path to settings.local.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print result JSON to stdout without writing")
    subparsers = parser.add_subparsers(dest="command")

    set_p = subparsers.add_parser("set", help="Set a key to a value")
    set_p.add_argument("key")
    set_p.add_argument("value", help="Value as JSON or string")

    rm_p = subparsers.add_parser("remove", help="Remove a key")
    rm_p.add_argument("key")

    merge_p = subparsers.add_parser("merge", help="Merge a JSON object")
    merge_p.add_argument("json_object", help="JSON object to merge")

    args = parser.parse_args()

    if args.command == "set":
        sys.exit(cmd_set(args.settings_file, args.key, args.value, args.dry_run))
    elif args.command == "remove":
        sys.exit(cmd_remove(args.settings_file, args.key, args.dry_run))
    elif args.command == "merge":
        sys.exit(cmd_merge(args.settings_file, args.json_object, args.dry_run))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
