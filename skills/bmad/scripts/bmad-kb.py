#!/usr/bin/env python3
"""
bmad-kb.py - BMAD knowledge-base (KB) preflight, freshness, and impact checks.

The KB is the pair of files the real BMAD-METHOD skills produce:
  - {project_knowledge}/index.md          (bmad-document-project)
  - {output_folder}/project-context.md    (bmad-generate-project-context)

Paths come from _bmad/bmm/config.yaml, falling back to _bmad/core/config.yaml,
then to BMAD defaults.

The freshness marker is <workstation>/avengers/kb.json when an md workstation is
set (mdWorkstation in .avengers/settings.json), else .avengers/kb.json. Reads fall
back to the legacy .avengers/kb.json; `stamp` moves it into the workstation. The
marker is keyed per branch so worktrees on different branches do not overwrite
each other:
  {"version": 2, "index_path", "context_path",
   "branches": {"<branch>": {"commit", "stamped_at", "arch_hashes"}}}
A detached HEAD uses the key HEAD@<sha7>.

Commands:
  preflight [--track T]  - Verify the project-level BMAD install (_bmad/)
  status                 - Report KB state as JSON (missing|unstamped|fresh|stale|unknown)
  impact --base SHA      - Report refresh-worthy change signals since SHA as JSON
  stamp [--dry-run]      - Record HEAD for the current branch as the KB freshness marker

Exit codes:
  0 = success
  1 = error
  2 = no-op (preflight: TEA module missing for --track full;
             impact: no commits since base; stamp: already stamped at HEAD)
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = {"project_knowledge": "docs", "output_folder": "_bmad-output"}
CONFIG_FILES = (Path("_bmad") / "bmm" / "config.yaml", Path("_bmad") / "core" / "config.yaml")
KB_MARKER = Path(".avengers") / "kb.json"
PROJECT_SETTINGS = Path(".avengers") / "settings.json"
WS_MARKER = Path("avengers") / "kb.json"
KB_RULES = Path(".claude") / "rules" / "avengers-kb.md"
WORKSTATION = (Path(__file__).resolve().parents[2] / "avengers-workstation" / "scripts"
               / "workstation.py")
OPTIONAL_KEYS = ("planning_artifacts",)
OPENSPEC_DIR = "openspec"
STALE_FILE_THRESHOLD = 20
TRACKS = ("quick", "standard", "full")

DEPENDENCY_MANIFESTS = {
    "package.json", "pyproject.toml", "go.mod", "Cargo.toml", "composer.json", "Gemfile",
}
API_CONTRACT_PATTERNS = ("openapi*", "swagger*", "*.proto", "*.graphql")
MIGRATION_DIRS = {"migrations", "migrate"}
BREAKING_SUBJECT = re.compile(r"^[A-Za-z]+(\([^)]*\))?!:")
BREAKING_BODY = re.compile(r"BREAKING[ -]CHANGE")



class KBError(Exception):
    """Unrecoverable error; main() prints it to stderr and exits 1."""


INSTALL_HINT = "BMAD-METHOD is not installed here. Run `npx bmad-method install` in the project root."
TEA_HINT = "Full track needs the TEA module (_bmad/tea/). Run `npx bmad-method install` and add TEA."


# --------------------------------------------------------------------------- config

def _strip_value(raw: str) -> str:
    """Strip quotes and inline comments from a flat YAML scalar."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        quote = raw[0]
        end = raw.find(quote, 1)
        return raw[1:end] if end != -1 else raw[1:]
    return re.split(r"\s+#", raw, maxsplit=1)[0].strip()


def parse_flat_yaml(path: Path) -> dict[str, str]:
    """Parse top-level `key: value` pairs. Nested blocks and lists are ignored."""
    result: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return result
    for line in text.splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = _strip_value(value)
        if value:
            result[key.strip()] = value
    return result


def _resolve_path(value: str, project_dir: Path) -> Path:
    value = value.replace("{project-root}", str(project_dir))
    path = Path(value)
    if not path.is_absolute():
        path = project_dir / path
    return path.resolve()


def read_bmad_config(project_dir: Path) -> dict[str, Path]:
    """Resolve project_knowledge and output_folder (bmm, then core, then defaults)."""
    merged: dict[str, str] = {}
    for rel in CONFIG_FILES:
        for key, value in parse_flat_yaml(project_dir / rel).items():
            merged.setdefault(key, value)

    resolved: dict[str, Path] = {}
    for key, default in DEFAULTS.items():
        if key not in merged:
            print(f"WARNING: '{key}' not set in _bmad config; using default '{default}'",
                  file=sys.stderr)
        resolved[key] = _resolve_path(merged.get(key, default), project_dir)
    for key in OPTIONAL_KEYS:
        if key in merged:
            output = str(resolved["output_folder"])
            resolved[key] = _resolve_path(merged[key].replace("{output_folder}", output),
                                          project_dir)
    return resolved


def read_workstation(project_dir: Path) -> Path | None:
    """The md workstation from .avengers/settings.json (no import of workstation.py)."""
    path = project_dir / PROJECT_SETTINGS
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("mdWorkstation")
    except (OSError, ValueError, UnicodeDecodeError, AttributeError):
        return None
    if not isinstance(value, str) or not value or value == "in-repo":
        return None
    ws = Path(value)
    if not ws.is_dir():
        print(f"WARNING: md workstation {ws} not found; using {KB_MARKER}", file=sys.stderr)
        return None
    return ws


def marker_rel(path: Path, project_dir: Path, ws: Path | None) -> str:
    """Marker path form: relative to the workstation when inside it, else to the project.

    With a workstation, in-repo paths are written as {project-root}/<rel> so the
    shared marker never carries a machine-specific absolute path.
    """
    if ws is None:
        return _rel(path, project_dir)
    try:
        return path.relative_to(Path(os.path.realpath(ws))).as_posix()
    except ValueError:
        rel = _rel(path, project_dir)
        return rel if Path(rel).is_absolute() else "{project-root}/" + rel


def kb_paths(project_dir: Path) -> tuple[Path, Path, dict[str, Path]]:
    config = read_bmad_config(project_dir)
    index = config["project_knowledge"] / "index.md"
    context = config["output_folder"] / "project-context.md"
    return index, context, config


def _rel(path: Path, project_dir: Path) -> str:
    try:
        return path.relative_to(project_dir).as_posix()
    except ValueError:
        return str(path)


def arch_hashes(config: dict[str, Path]) -> dict[str, str]:
    """sha256 of *architecture*.md under planning_artifacts and output_folder.

    <output_folder>/openspec/ is skipped: with an md workstation it holds the OpenSpec
    changes and specs (workstation.py's openspec link), which are not BMAD architecture.
    """
    output = config["output_folder"]
    hashes: dict[str, str] = {}
    for key in ("planning_artifacts", "output_folder"):
        root = config.get(key)
        if root is None or not root.is_dir():
            continue
        for path in sorted(root.rglob("*architecture*.md")):
            if path.is_relative_to(output / OPENSPEC_DIR):
                continue
            if path.is_file():
                hashes[_rel(path, output)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def arch_hash_signals(stored: dict | None, current: dict[str, str]) -> list[dict[str, str]]:
    """Architecture signals from hash differences (no baseline stored -> no signal)."""
    if not isinstance(stored, dict):
        return []
    signals = []
    for rel in sorted(set(stored) | set(current)):
        if stored.get(rel) == current.get(rel):
            continue
        change = ("added" if rel not in stored else
                  "removed" if rel not in current else "content changed")
        signals.append({"type": "architecture", "detail": f"{rel} ({change})"})
    return signals


# --------------------------------------------------------------------------- git

def run_git(project_dir: Path, *args: str) -> subprocess.CompletedProcess | None:
    """Run git with an argument list (no shell). None when git is unavailable."""
    try:
        return subprocess.run(
            ["git", "-C", str(project_dir), *args],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None


def git_head(project_dir: Path) -> str | None:
    proc = run_git(project_dir, "rev-parse", "--verify", "HEAD")
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def git_commit_exists(project_dir: Path, sha: str) -> str | None:
    proc = run_git(project_dir, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _nul_split(proc: subprocess.CompletedProcess | None) -> list[str]:
    """Split -z output (NUL-separated, unquoted paths) into a list."""
    if proc is None or proc.returncode != 0:
        return []
    return [entry for entry in proc.stdout.split("\0") if entry]


def git_branch(project_dir: Path) -> str | None:
    """Current branch name, HEAD@<sha7> when detached, None outside git."""
    proc = run_git(project_dir, "symbolic-ref", "--short", "-q", "HEAD")
    if proc is not None and proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    head = git_head(project_dir)
    return f"HEAD@{head[:7]}" if head else None


def output_outside_git(project_dir: Path, config: dict[str, Path]) -> bool:
    """True when output_folder resolves outside the project's git work tree."""
    proc = run_git(project_dir, "rev-parse", "--show-toplevel")
    if proc is None or proc.returncode != 0:
        return False
    top = Path(os.path.realpath(proc.stdout.strip()))
    try:
        config["output_folder"].relative_to(top)
        return False
    except ValueError:
        return True


def git_count_since(project_dir: Path, base: str) -> int:
    proc = run_git(project_dir, "rev-list", "--count", f"{base}..HEAD")
    if proc is None or proc.returncode != 0:
        return 0
    return int(proc.stdout.strip() or 0)


# --------------------------------------------------------------------------- signals

def excluded_prefixes(project_dir: Path, config: dict[str, Path]) -> list[str]:
    prefixes = [".avengers/", "_bmad/"]
    for key in ("project_knowledge", "output_folder"):
        rel = _rel(config[key], project_dir)
        if rel not in ("", ".") and not Path(rel).is_absolute():
            prefixes.append(rel.rstrip("/") + "/")
    return prefixes


def is_excluded(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _file_signal(path: str) -> dict[str, str] | None:
    name = path.rsplit("/", 1)[-1]
    parts = path.split("/")
    if name in DEPENDENCY_MANIFESTS or fnmatch.fnmatch(name, "requirements*.txt"):
        return {"type": "dependencies", "detail": path}
    if any(part in MIGRATION_DIRS for part in parts[:-1]):
        return {"type": "migration", "detail": path}
    if any(fnmatch.fnmatch(name, pattern) for pattern in API_CONTRACT_PATTERNS):
        return {"type": "api_contract", "detail": path}
    return None


def collect_signals(project_dir: Path, base: str, config: dict[str, Path]) -> dict:
    """Collect refresh-worthy signals between base and HEAD.

    Returns {signals, changed_files, changed_areas}. changed_files excludes the
    KB dirs, output_folder, .avengers/ and _bmad/.
    """
    signals: list[dict[str, str]] = []

    # Path-limited to the project dir so monorepo commits elsewhere are not flagged.
    log = run_git(project_dir, "log", "--format=%h%x1f%s%x1f%b%x1e", f"{base}..HEAD", "--", ".")
    for record in (log.stdout if log and log.returncode == 0 else "").split("\x1e"):
        fields = record.strip("\n").split("\x1f")
        if len(fields) < 3:
            continue
        short, subject, body = fields[0], fields[1], fields[2]
        if BREAKING_SUBJECT.match(subject) or BREAKING_BODY.search(body):
            signals.append({"type": "breaking_change", "detail": f"{short} {subject}"})

    # -z: NUL-separated, unquoted paths (non-ASCII names are not octal-escaped).
    all_files = _nul_split(run_git(project_dir, "diff", "--name-only", "-z", "--relative",
                                   base, "HEAD"))

    output_rel = _rel(config["output_folder"], project_dir).rstrip("/") + "/"
    for path in all_files:
        name = path.rsplit("/", 1)[-1]
        if path.startswith(output_rel) and fnmatch.fnmatch(name, "*architecture*.md"):
            signals.append({"type": "architecture", "detail": path})

    prefixes = excluded_prefixes(project_dir, config)
    changed = [f for f in all_files if not is_excluded(f, prefixes)]

    for path in changed:
        signal = _file_signal(path)
        if signal:
            signals.append(signal)

    base_entries = set(_nul_split(run_git(project_dir, "ls-tree", "--name-only", "-z", base)))
    new_dirs = sorted({
        f.split("/", 1)[0] for f in changed
        if "/" in f and not f.startswith(".") and f.split("/", 1)[0] not in base_entries
    })
    for new_dir in new_dirs:
        signals.append({"type": "new_top_level_dir", "detail": new_dir + "/"})

    if len(changed) >= STALE_FILE_THRESHOLD:
        signals.append({"type": "volume", "detail": f"{len(changed)} files changed"})

    areas = sorted({f.split("/", 1)[0] if "/" in f else "." for f in changed})
    return {"signals": signals, "changed_files": changed, "changed_areas": areas}


# --------------------------------------------------------------------------- marker

def marker_locations(project_dir: Path, ws: Path | None) -> tuple[Path, Path]:
    """(primary, legacy). Without a workstation both are .avengers/kb.json."""
    legacy = project_dir / KB_MARKER
    return (ws / WS_MARKER if ws else legacy), legacy


def read_marker(project_dir: Path, ws: Path | None = None) -> tuple[dict | None, Path | None]:
    """Read the marker from the workstation, falling back to the legacy location.

    Returns (data, path read). A flat legacy marker ({commit, ...}) is kept under
    "legacy" and applies to whichever branch reads it.
    """
    for marker in dict.fromkeys(marker_locations(project_dir, ws)):
        data = _load_marker(marker, project_dir)
        if data is None:
            continue
        if "branches" not in data:
            data = {"branches": {}, "legacy": data} if data.get("commit") else {"branches": {}}
        if not isinstance(data.get("branches"), dict):
            data["branches"] = {}
        return data, marker
    return None, None


def pick_entry(marker: dict | None, branch: str | None) -> tuple[dict | None, bool]:
    """(entry, is_fallback). Fallback = the newest other branch's entry."""
    if not marker:
        return None, False
    branches = marker.get("branches") or {}
    if branch and isinstance(branches.get(branch), dict):
        return branches[branch], False
    if marker.get("legacy"):
        return marker["legacy"], False
    others = [e for e in branches.values() if isinstance(e, dict) and e.get("commit")]
    if others:
        return max(others, key=lambda e: str(e.get("stamped_at", ""))), True
    return None, False


def _load_marker(marker: Path, project_dir: Path) -> dict | None:
    """Load one marker file. Malformed files are backed up to kb.json.bak."""
    if not marker.exists():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("kb.json is not a JSON object")
        return data
    except (ValueError, UnicodeDecodeError) as exc:
        backup = marker.with_name("kb.json.bak")
        shown = _rel(marker, project_dir)
        try:
            marker.replace(backup)
        except OSError as move_exc:
            raise KBError(f"malformed {shown} and cannot back it up: {move_exc}") from exc
        print(f"WARNING: malformed {shown} ({exc}); backed up to {_rel(backup, project_dir)}",
              file=sys.stderr)
        return None


def refresh_kb_rules(project_dir: Path) -> None:
    """Rewrite .claude/rules/avengers-kb.md (search hint + project-context.md import).

    The file has one generator, `workstation.py kb-rules`, shared with `workstation.py set`.
    """
    if not WORKSTATION.is_file():
        print(f"WARNING: {WORKSTATION} not found; {KB_RULES} not refreshed", file=sys.stderr)
        return
    proc = subprocess.run([sys.executable, str(WORKSTATION), "kb-rules",
                           "--project-dir", str(project_dir)],
                          capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        print(f"Refreshed {KB_RULES.as_posix()}")
    elif proc.returncode != 2:
        print(f"WARNING: could not refresh {KB_RULES}: {proc.stderr.strip()}", file=sys.stderr)


# --------------------------------------------------------------------------- commands

def cmd_preflight(project_dir: Path, track: str | None) -> int:
    if not (project_dir / "_bmad").is_dir():
        print("BMAD_MISSING")
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
        return 1
    if track == "full" and not (project_dir / "_bmad" / "tea").is_dir():
        print("TEA_MISSING")
        print(TEA_HINT, file=sys.stderr)
        return 2
    print("BMAD_OK")
    return 0


def cmd_status(project_dir: Path) -> int:
    if not (project_dir / "_bmad").is_dir():
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
        return 1

    index, context, config = kb_paths(project_dir)
    ws = read_workstation(project_dir)
    head = git_head(project_dir)
    branch = git_branch(project_dir)
    report = {
        "state": None,
        "index_path": marker_rel(index, project_dir, ws),
        "context_path": marker_rel(context, project_dir, ws),
        "workstation": str(ws) if ws else None,
        "branch": branch,
        "marker_path": None,
        "stamped_commit": None,
        "head": head,
        "commits_since": None,
        "signals": [],
    }

    marker, marker_path = read_marker(project_dir, ws) if index.exists() else (None, None)
    entry, fallback = pick_entry(marker, branch)
    stamped = entry.get("commit") if entry else None
    report["stamped_commit"] = stamped
    report["marker_path"] = str(marker_path) if marker_path else None

    if not index.exists():
        report["state"] = "missing"
    elif not stamped:
        report["state"] = "unstamped"
    elif head is None:
        report["state"] = "unknown"
    elif fallback:
        report["state"] = "stale"
        report["signals"] = [{"type": "branch_unstamped",
                              "detail": f"no stamp for branch {branch}; newest stamp is "
                                        f"{str(stamped)[:12]}"}]
    elif (resolved := git_commit_exists(project_dir, str(stamped))) is None:
        report["state"] = "stale"
        report["signals"] = [{"type": "unknown_stamp",
                              "detail": f"stamped commit {stamped} not found in history"}]
    else:
        report["commits_since"] = git_count_since(project_dir, resolved)
        found = collect_signals(project_dir, resolved, config)
        report["signals"] = found["signals"]
        if output_outside_git(project_dir, config):
            report["signals"] += arch_hash_signals(entry.get("arch_hashes"), arch_hashes(config))
        report["state"] = "stale" if report["signals"] else "fresh"

    print(json.dumps(report, indent=2))
    return 0


def cmd_impact(project_dir: Path, base: str) -> int:
    if git_head(project_dir) is None:
        print("ERROR: not a git repository (or no commits)", file=sys.stderr)
        return 1
    resolved = git_commit_exists(project_dir, base)
    if resolved is None:
        print(f"ERROR: unknown commit '{base}'", file=sys.stderr)
        return 1

    if git_count_since(project_dir, resolved) == 0:
        print(json.dumps({"refresh_recommended": False, "signals": [], "changed_areas": []},
                         indent=2))
        print(f"No commits since {base} (no-op)", file=sys.stderr)
        return 2

    _, _, config = kb_paths(project_dir)
    found = collect_signals(project_dir, resolved, config)
    if output_outside_git(project_dir, config):
        ws = read_workstation(project_dir)
        marker, _ = read_marker(project_dir, ws)
        entry, fallback = pick_entry(marker, git_branch(project_dir))
        if entry and not fallback:
            found["signals"] += arch_hash_signals(entry.get("arch_hashes"), arch_hashes(config))
    print(json.dumps({
        "refresh_recommended": bool(found["signals"]),
        "signals": found["signals"],
        "changed_areas": found["changed_areas"],
    }, indent=2))
    return 0


def cmd_stamp(project_dir: Path, dry_run: bool) -> int:
    head = git_head(project_dir)
    if head is None:
        print("ERROR: not a git repository (or no commits); cannot stamp", file=sys.stderr)
        return 1

    index, context, config = kb_paths(project_dir)
    ws = read_workstation(project_dir)
    branch = git_branch(project_dir) or "HEAD"
    target, legacy = marker_locations(project_dir, ws)
    marker, source = read_marker(project_dir, ws)
    hashes = arch_hashes(config)
    entry = ((marker or {}).get("branches") or {}).get(branch)
    if (source == target and isinstance(entry, dict) and entry.get("commit") == head
            and entry.get("arch_hashes") == hashes and not (marker or {}).get("legacy")):
        print(f"KB already stamped at {head[:12]} for {branch} (no-op)", file=sys.stderr)
        if ws:
            refresh_kb_rules(project_dir)
        return 2
    if not index.exists():
        print(f"WARNING: KB index not found at {_rel(index, project_dir)}", file=sys.stderr)

    branches = dict((marker or {}).get("branches") or {})
    branches[branch] = {
        "commit": head,
        "stamped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "arch_hashes": hashes,
    }
    payload = {
        "version": 2,
        "index_path": marker_rel(index, project_dir, ws),
        "context_path": marker_rel(context, project_dir, ws),
        "branches": branches,
    }
    content = json.dumps(payload, indent=2) + "\n"
    if dry_run:
        print(content, end="")
        return 0

    shown = _rel(target, project_dir)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if source == legacy and target != legacy:
            legacy.unlink()
            print(f"Moved legacy {KB_MARKER.as_posix()} into the workstation")
    except OSError as exc:
        print(f"ERROR: cannot write {shown}: {exc}", file=sys.stderr)
        return 1
    print(f"Stamped KB at {head[:12]} for {branch} -> {shown}")
    if ws:
        refresh_kb_rules(project_dir)
    return 0


# --------------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BMAD knowledge-base preflight, freshness, and impact checks.",
        epilog="Exit codes: 0 = success, 1 = error, 2 = no-op.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-dir", type=Path, default=Path("."),
                        help="Project root directory (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", parents=[common],
                         help="Verify _bmad/ exists (and _bmad/tea/ for --track full)",
                         description="Exit 0 if _bmad/ exists, 1 if missing, "
                                     "2 (TEA_MISSING) if --track full and _bmad/tea/ is missing.")
    pre.add_argument("--track", choices=TRACKS, help="Relay track to check prerequisites for")

    sub.add_parser("status", parents=[common],
                   help="Print KB state as JSON",
                   description="Print {state, index_path, context_path, workstation, branch, "
                               "marker_path, stamped_commit, head, commits_since, signals}. "
                               "Paths are relative to the workstation when one is set. "
                               "Exit 0; 1 if _bmad/ is missing.")

    imp = sub.add_parser("impact", parents=[common],
                         help="Print refresh-worthy change signals since a commit as JSON",
                         description="Print {refresh_recommended, signals, changed_areas}. "
                                     "Exit 0; 2 if no commits since base; 1 on a bad sha.")
    imp.add_argument("--base", required=True, help="Base commit (e.g. kb_base_commit)")

    stamp = sub.add_parser("stamp", parents=[common],
                           help="Record HEAD for the current branch in the KB marker",
                           description="Write the KB marker (<workstation>/avengers/kb.json, "
                                       "else .avengers/kb.json) recording HEAD for the current "
                                       "branch, and refresh .claude/rules/avengers-kb.md when "
                                       "a workstation is set. Exit 0; 2 if already stamped at "
                                       "HEAD; 1 on error.")
    stamp.add_argument("--dry-run", action="store_true", help="Print the JSON instead of writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_dir = args.project_dir.resolve()
    if not project_dir.is_dir():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1

    try:
        if args.command == "preflight":
            return cmd_preflight(project_dir, args.track)
        if args.command == "status":
            return cmd_status(project_dir)
        if args.command == "impact":
            return cmd_impact(project_dir, args.base)
        return cmd_stamp(project_dir, args.dry_run)
    except KBError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
