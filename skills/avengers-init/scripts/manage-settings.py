#!/usr/bin/env python3
"""
manage-settings.py - Manage .claude/settings.local.json for a project.

Adds or removes keys from settings.local.json without clobbering existing content.
Supports --dry-run: prints the resulting JSON to stdout without writing.

list-add / list-remove edit a list at a dotted key path (for example
permissions.additionalDirectories) without touching sibling keys, so they are
safe where the shallow `merge` would wipe permissions.allow / permissions.deny.

Exit codes:
  0 = success (or dry-run complete)
  1 = error
  2 = no-op (key already set to that value; list value already present/absent)
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


def _walk(settings: dict, dotted: str, create: bool):
    """Return (parent_dict, leaf_key, chain) for a dotted key path.

    chain is the list of (dict, key) pairs from the root to the leaf, used to
    prune dicts that become empty. Returns (None, leaf, chain) when an
    intermediate key is missing and create is False.
    """
    parts = [part for part in dotted.split(".") if part]
    if not parts:
        raise ValueError("empty key")
    node = settings
    chain = []
    for part in parts[:-1]:
        child = node.get(part)
        if child is None:
            if not create:
                return None, parts[-1], chain
            child = node[part] = {}
        elif not isinstance(child, dict):
            raise ValueError(f"'{part}' in '{dotted}' is not an object")
        chain.append((node, part))
        node = child
    return node, parts[-1], chain


def _emit(settings_path: Path, settings: dict, dry_run: bool, message: str) -> int:
    output = json.dumps(settings, indent=2)
    if dry_run:
        print(output)
        return 0
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(output)
    print(message)
    return 0


def cmd_list_add(settings_path: Path, key: str, value: str, dry_run: bool) -> int:
    """Append value to the list at a dotted key path (deduplicated, order kept)."""
    settings = load_settings(settings_path)
    try:
        parent, leaf, _ = _walk(settings, key, create=True)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    current = parent.get(leaf, [])
    if not isinstance(current, list):
        print(f"ERROR: '{key}' exists and is not a list", file=sys.stderr)
        return 1
    if value in current:
        print(f"'{value}' already in '{key}' (no-op)", file=sys.stderr)
        return 2
    parent[leaf] = [*current, value]
    return _emit(settings_path, settings, dry_run, f"Added '{value}' to '{key}' in {settings_path}")


def cmd_list_remove(settings_path: Path, key: str, value: str, dry_run: bool) -> int:
    """Remove value from the list at a dotted key path. Empty lists/objects are pruned."""
    settings = load_settings(settings_path)
    try:
        parent, leaf, chain = _walk(settings, key, create=False)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    current = parent.get(leaf) if parent is not None else None
    if not isinstance(current, list) or value not in current:
        print(f"'{value}' not in '{key}' (no-op)", file=sys.stderr)
        return 2
    remaining = [item for item in current if item != value]
    if remaining:
        parent[leaf] = remaining
    else:
        del parent[leaf]
        for owner, part in reversed(chain):
            if owner[part]:
                break
            del owner[part]
    return _emit(settings_path, settings, dry_run,
                 f"Removed '{value}' from '{key}' in {settings_path}")


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

    merge_p = subparsers.add_parser("merge", help="Merge a JSON object (shallow, top-level)")
    merge_p.add_argument("json_object", help="JSON object to merge")

    for name, help_text in (("list-add", "Add a value to a list at a dotted key path"),
                            ("list-remove", "Remove a value from a list at a dotted key path")):
        list_p = subparsers.add_parser(
            name, help=help_text,
            description=f"{help_text}. Sibling keys are untouched. "
                        "Exit 0 = changed (or dry-run printed), 1 = error, 2 = no-op.")
        list_p.add_argument("--key", required=True,
                            help="Dotted key path, e.g. permissions.additionalDirectories")
        list_p.add_argument("--value", required=True, help="String value to add or remove")
        # SUPPRESS keeps the top-level --dry-run / --settings-file working as well.
        list_p.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS,
                            help="Print result JSON to stdout without writing")
        list_p.add_argument("--settings-file", type=Path, default=argparse.SUPPRESS,
                            help="Path to settings.local.json")

    args = parser.parse_args()

    if args.command == "set":
        sys.exit(cmd_set(args.settings_file, args.key, args.value, args.dry_run))
    elif args.command == "remove":
        sys.exit(cmd_remove(args.settings_file, args.key, args.dry_run))
    elif args.command == "merge":
        sys.exit(cmd_merge(args.settings_file, args.json_object, args.dry_run))
    elif args.command == "list-add":
        sys.exit(cmd_list_add(args.settings_file, args.key, args.value, args.dry_run))
    elif args.command == "list-remove":
        sys.exit(cmd_list_remove(args.settings_file, args.key, args.value, args.dry_run))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
