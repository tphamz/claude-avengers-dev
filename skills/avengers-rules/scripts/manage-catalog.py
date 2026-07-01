#!/usr/bin/env python3
"""
manage-catalog.py - Manage project rules catalog.

Commands:
  list    - Show available and installed rules
  install - Copy a rule from plugin to project .claude/rules/
  remove  - Remove a rule from project .claude/rules/

Exit codes:
  0 = success
  1 = error
  2 = no-op (already installed / not installed)
"""
import argparse
import shutil
import sys
from pathlib import Path


def cmd_list(plugin_dir: Path, project_dir: Path) -> int:
    """List available and installed rules."""
    plugin_rules_dir = plugin_dir / ".claude" / "rules"
    project_rules_dir = project_dir / ".claude" / "rules"

    # Available rules from plugin
    available: dict[str, Path] = {}
    if plugin_rules_dir.exists():
        for f in plugin_rules_dir.glob("*.md"):
            available[f.stem] = f

    # Installed rules in project
    installed: dict[str, Path] = {}
    if project_rules_dir.exists():
        for f in project_rules_dir.glob("*.md"):
            installed[f.stem] = f

    all_names = sorted(set(available) | set(installed))

    if not all_names:
        print("No rules found.")
        return 0

    print("Rules:")
    for name in all_names:
        if name in installed and name in available:
            print(f"  ✓ {name} (installed)")
        elif name in installed:
            print(f"  * {name} (custom - not from plugin)")
        else:
            print(f"    {name} (available)")

    return 0


def cmd_install(plugin_dir: Path, project_dir: Path, rule_name: str) -> int:
    """Install a rule from plugin to project."""
    plugin_rules_dir = plugin_dir / ".claude" / "rules"
    project_rules_dir = project_dir / ".claude" / "rules"

    src = plugin_rules_dir / f"{rule_name}.md"
    if not src.exists():
        print(f"ERROR: Rule '{rule_name}' not found in plugin", file=sys.stderr)
        print(f"Available: {[f.stem for f in plugin_rules_dir.glob('*.md')]}", file=sys.stderr)
        return 1

    dst = project_rules_dir / f"{rule_name}.md"
    if dst.exists():
        print(f"Rule '{rule_name}' already installed (no-op)", file=sys.stderr)
        return 2

    project_rules_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Installed: .claude/rules/{rule_name}.md")
    return 0


def cmd_remove(plugin_dir: Path, project_dir: Path, rule_name: str) -> int:
    """Remove a rule from project."""
    project_rules_dir = project_dir / ".claude" / "rules"
    target = project_rules_dir / f"{rule_name}.md"

    if not target.exists():
        print(f"Rule '{rule_name}' not installed (no-op)", file=sys.stderr)
        return 2

    target.unlink()
    print(f"Removed: .claude/rules/{rule_name}.md")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage project rules catalog")
    parser.add_argument("command", choices=["list", "install", "remove"])
    parser.add_argument("rule_name", nargs="?", help="Rule name (required for install/remove)")
    parser.add_argument("--plugin-dir", type=Path, required=True, help="Plugin root directory")
    parser.add_argument("--project-dir", type=Path, required=True, help="Project root directory")
    args = parser.parse_args()

    if args.command in ("install", "remove") and not args.rule_name:
        print(f"ERROR: rule_name required for '{args.command}'", file=sys.stderr)
        sys.exit(1)

    plugin_dir = args.plugin_dir.resolve()
    project_dir = args.project_dir.resolve()

    if args.command == "list":
        sys.exit(cmd_list(plugin_dir, project_dir))
    elif args.command == "install":
        sys.exit(cmd_install(plugin_dir, project_dir, args.rule_name))
    elif args.command == "remove":
        sys.exit(cmd_remove(plugin_dir, project_dir, args.rule_name))


if __name__ == "__main__":
    main()
