#!/usr/bin/env python3
"""
sdd-openspec.py - Guarded wrapper around the OpenSpec CLI for the /sdd relay.

OpenSpec (https://github.com/Fission-AI/OpenSpec, MIT) is a separate install; this
script never installs it. It always calls `openspec` with an argument list, reads
its --json output, and sets OPENSPEC_TELEMETRY=0 and DO_NOT_TRACK=1 on every call.

The guards cover gaps found in OpenSpec 1.13.2:
  - `validate --strict` passes a change that `archive` will later refuse; that case
    is only an INFO issue ("Archive would refuse this delta", "Could not check
    archive merge conflicts"). `validate` here treats both as failures.
  - `archive -y` archives a change with incomplete tasks. `archive` here refuses
    unless every task is done (or --allow-incomplete with a reason).
  - `archive` reports its refusals in the --json `status[]` list. Empty output,
    `archive: null`, or any error entry is a failure here.
  - `init` ("Path is outside the allowed directory") and `archive`
    (archive_path_outside_root) refuse an openspec/ symlink that points outside the
    project - exactly the md workstation layout. Every call here therefore runs
    from the real parent of openspec/ (the workstation), where openspec/ is a real
    directory inside the OpenSpec root.

Commands:
  preflight                         Check openspec (>= 1.13) and git (>= 2.31)
  init [--dry-run]                  openspec init --tools none + the avengers-sdd schema
  new <change> --schema S           Create a change pinned to schema S
  validate <change>                 Strict validation, archive refusals included
  status <change>                   Artifacts, task counts, next step, change_dir_real
  instructions <artifact> <change>  OpenSpec's instructions for an artifact (or apply)
  archive <change>                  Guarded archive (tasks complete, validate, archive)

Exit codes:
  0 = success
  1 = error (or: preflight requirement missing, validation failed, archive refused)
  2 = no-op (init: config.yaml and the avengers-sdd schema already exist)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_NAME = "avengers-sdd"
SCHEMA_SOURCE = PLUGIN_ROOT / "references" / "sdd" / "schemas" / SCHEMA_NAME
OPENSPEC_DIR = "openspec"
MIN_OPENSPEC = (1, 13)
MIN_GIT = (2, 31)
PINNED_OPENSPEC = "1.13.2"
TELEMETRY_ENV = {"OPENSPEC_TELEMETRY": "0", "DO_NOT_TRACK": "1"}
INSTALL_HINT = ("OpenSpec is not installed (or is older than 1.13). Install it with "
                "`npm i -g @fission-ai/openspec@latest`, then re-run.")
CHANGE_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# INFO messages from OpenSpec's validator (dist/core/validation/validator.js, 1.13.2)
# that mean `archive` will refuse the change.
ARCHIVE_BLOCKERS = ("Archive would refuse this delta", "Could not check archive merge conflicts")
TIMEOUT = 300


class SDDError(Exception):
    """Unrecoverable error; main() prints it to stderr and exits 1."""


# --------------------------------------------------------------------------- process

def openspec_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(TELEMETRY_ENV)
    return env


def find_openspec(project_dir: Path) -> Path | None:
    """`openspec` on PATH, else the project's node_modules/.bin/openspec."""
    found = shutil.which("openspec")
    if found:
        return Path(found)
    local = project_dir / "node_modules" / ".bin" / "openspec"
    return local if local.is_file() and os.access(local, os.X_OK) else None


def require_openspec(project_dir: Path) -> Path:
    binary = find_openspec(project_dir)
    if binary is None:
        raise SDDError(INSTALL_HINT)
    return binary


def openspec_cwd(project_dir: Path) -> Path:
    """Where to run openspec: the real parent of a symlinked openspec/, else the project.

    OpenSpec 1.13.2 refuses to init or archive through an openspec/ symlink that leaves
    the project. From the symlink target's parent (the md workstation), openspec/ is a
    real directory inside the OpenSpec root, so every command works there.
    """
    root = project_dir / OPENSPEC_DIR
    if not root.is_symlink():
        return project_dir
    if not root.exists():
        raise SDDError(f"{OPENSPEC_DIR}/ is a dangling symlink to {os.readlink(root)}; run "
                       "`workstation.py set --path <workstation> --link openspec` first (it "
                       "creates the target)")
    real = Path(os.path.realpath(root))
    if real.name != OPENSPEC_DIR:
        raise SDDError(f"{OPENSPEC_DIR}/ links to {real}, which is not named "
                       f"'{OPENSPEC_DIR}'; OpenSpec cannot use it as its root")
    return real.parent


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, cwd=cwd, env=openspec_env(), capture_output=True,
                              text=True, check=False, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SDDError(f"could not run {argv[0]}: {exc}") from exc


def openspec_json(project_dir: Path, *args: str) -> tuple[int, dict | None, str]:
    """Run `openspec <args>`; return (exit code, parsed stdout JSON or None, stderr)."""
    proc = run([str(require_openspec(project_dir)), *args], openspec_cwd(project_dir))
    data = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            data = parsed if isinstance(parsed, dict) else None
        except ValueError:
            data = None
    return proc.returncode, data, proc.stderr.strip()


def status_errors(data: dict | None) -> list[dict]:
    """The error entries of an OpenSpec --json `status[]` list."""
    entries = (data or {}).get("status") or []
    return [e for e in entries if isinstance(e, dict) and e.get("severity") == "error"]


def format_errors(errors: list[dict]) -> str:
    lines = []
    for entry in errors:
        line = f"[{entry.get('code', 'error')}] {entry.get('message', '')}".rstrip()
        if entry.get("fix"):
            line += f" (fix: {entry['fix']})"
        lines.append(line)
    return "; ".join(lines)


def fail_on(code: int, data: dict | None, stderr: str, what: str) -> dict:
    """Return the JSON payload, or raise with OpenSpec's own error text."""
    errors = status_errors(data)
    if errors:
        raise SDDError(f"{what} failed: {format_errors(errors)}")
    if data is None:
        detail = f": {stderr}" if stderr else ""
        raise SDDError(f"{what} printed no JSON (exit {code}){detail}")
    if code != 0:
        raise SDDError(f"{what} exited {code}" + (f": {stderr}" if stderr else ""))
    return data


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


# --------------------------------------------------------------------------- versions

def parse_version(text: str) -> tuple[int, ...] | None:
    """First dotted version in text: 'openspec v1.13.2' -> (1, 13, 2)."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def version_str(version: tuple[int, ...] | None) -> str | None:
    return ".".join(str(part) for part in version) if version else None


def cmd_preflight(project_dir: Path) -> int:
    report: dict = {"openspec": {"path": None, "version": None, "ok": False,
                                 "min": version_str(MIN_OPENSPEC), "pinned": PINNED_OPENSPEC},
                    "git": {"version": None, "ok": False, "min": version_str(MIN_GIT)},
                    "bmad": (project_dir / "_bmad").is_dir(),
                    "tea": (project_dir / "_bmad" / "tea").is_dir()}
    binary = find_openspec(project_dir)
    if binary is not None:
        proc = run([str(binary), "--version"], project_dir)
        version = parse_version(proc.stdout) if proc.returncode == 0 else None
        report["openspec"].update(path=str(binary), version=version_str(version),
                                  ok=bool(version and version[:2] >= MIN_OPENSPEC))
    try:
        git = subprocess.run(["git", "--version"], capture_output=True, text=True,
                             check=False, timeout=TIMEOUT)
        git_version = parse_version(git.stdout) if git.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        git_version = None
    report["git"].update(version=version_str(git_version),
                         ok=bool(git_version and git_version[:2] >= MIN_GIT))
    emit(report)
    if not report["openspec"]["ok"]:
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
    if not report["git"]["ok"]:
        print(f"ERROR: git {version_str(MIN_GIT)} or later is required", file=sys.stderr)
    return 0 if report["openspec"]["ok"] and report["git"]["ok"] else 1


# --------------------------------------------------------------------------- init

def set_default_schema(config: Path, schema: str) -> None:
    lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if re.match(r"^schema\s*:", line):
            lines[i] = f"schema: {schema}\n"
            break
    else:
        lines.insert(0, f"schema: {schema}\n")
    config.write_text("".join(lines), encoding="utf-8")


def cmd_init(project_dir: Path, dry_run: bool) -> int:
    root = project_dir / OPENSPEC_DIR
    if root.is_symlink() and not root.exists():
        raise SDDError(f"{OPENSPEC_DIR}/ is a dangling symlink to {os.readlink(root)}; run "
                       "`workstation.py set --path <workstation> --link openspec` first (it "
                       "creates the target), then re-run init")
    if root.exists() and not root.is_dir():
        raise SDDError(f"{OPENSPEC_DIR} exists and is not a directory")
    if not SCHEMA_SOURCE.is_dir():
        raise SDDError(f"plugin schema not found: {SCHEMA_SOURCE}")
    config = root / "config.yaml"
    schema_dir = root / "schemas" / SCHEMA_NAME
    if config.is_file() and schema_dir.is_dir():
        print(f"{OPENSPEC_DIR}/config.yaml and the {SCHEMA_NAME} schema already exist (no-op)",
              file=sys.stderr)
        return 2

    create_config = not config.is_file()
    actions = []
    if create_config:
        actions += ["run `openspec init --tools none`",
                    f"set the default schema in {OPENSPEC_DIR}/config.yaml to {SCHEMA_NAME}"]
    if not schema_dir.is_dir():
        actions.append(f"install the {SCHEMA_NAME} schema into {OPENSPEC_DIR}/schemas/")
    if not dry_run:
        binary = require_openspec(project_dir)
        if create_config:
            # --tools none writes only config.yaml, specs/ and changes/archive/: no /opsx
            # commands or skills, so nothing can bypass the relay.
            cwd = openspec_cwd(project_dir)
            proc = run([str(binary), "init", "--tools", "none", "--no-animation"], cwd)
            if proc.returncode != 0 or not config.is_file():
                detail = (proc.stderr or proc.stdout).strip()
                raise SDDError(f"openspec init failed (exit {proc.returncode})"
                               + (f": {detail}" if detail else ""))
            set_default_schema(config, SCHEMA_NAME)
        if not schema_dir.is_dir():
            schema_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(SCHEMA_SOURCE, schema_dir)
    emit({"actions": actions, "openspec_dir_real": os.path.realpath(root), "dry_run": dry_run})
    return 0


# --------------------------------------------------------------------------- new

def check_name(change: str) -> None:
    if not CHANGE_NAME.match(change):
        raise SDDError(f"invalid change name '{change}': use kebab-case (lowercase letters, "
                       "digits and single hyphens), e.g. add-user-export")


def cmd_new(project_dir: Path, change: str, schema: str) -> int:
    check_name(change)
    code, data, stderr = openspec_json(project_dir, "new", "change", change,
                                       "--schema", schema, "--json")
    payload = fail_on(code, data, stderr, "openspec new change")
    created = payload.get("change") or {}
    if not created.get("path"):
        raise SDDError("openspec new change reported no change path")
    emit({"change": created.get("id", change), "schema": created.get("schema", schema),
          "path": created["path"], "change_dir_real": os.path.realpath(created["path"])})
    return 0


# --------------------------------------------------------------------------- validate

def validate_change(project_dir: Path, change: str) -> dict:
    """{change, valid, openspec_valid, issues, blocking}; valid folds in archive refusals."""
    code, data, stderr = openspec_json(project_dir, "validate", change, "--type", "change",
                                       "--strict", "--json", "--no-interactive")
    errors = status_errors(data)
    if errors:
        raise SDDError(f"openspec validate failed: {format_errors(errors)}")
    items = (data or {}).get("items")
    if not isinstance(items, list):
        detail = f": {stderr}" if stderr else ""
        raise SDDError(f"openspec validate printed no result (exit {code}){detail}")
    item = next((i for i in items if isinstance(i, dict) and i.get("id") == change), None)
    if item is None:
        raise SDDError(f"openspec validate returned no result for '{change}'")
    issues = [{"level": str(i.get("level", "")).upper(), "path": i.get("path"),
               "message": i.get("message", "")}
              for i in item.get("issues") or [] if isinstance(i, dict)]
    blocking = [i for i in issues if i["level"] in ("ERROR", "WARNING")
                or any(str(i["message"]).startswith(b) for b in ARCHIVE_BLOCKERS)]
    openspec_valid = bool(item.get("valid"))
    return {"change": change, "valid": openspec_valid and not blocking,
            "openspec_valid": openspec_valid, "issues": issues, "blocking": blocking}


def print_blocking(report: dict) -> None:
    for issue in report["blocking"]:
        print(f"INVALID: [{issue['level']}] {issue['path']}: {issue['message']}",
              file=sys.stderr)
    if report["openspec_valid"] and report["blocking"]:
        print("NOTE: openspec validate --strict passed, but archive would refuse this change",
              file=sys.stderr)


def cmd_validate(project_dir: Path, change: str) -> int:
    check_name(change)
    report = validate_change(project_dir, change)
    emit(report)
    if not report["valid"]:
        print_blocking(report)
        return 1
    return 0


# --------------------------------------------------------------------------- status

def task_counts(project_dir: Path, change: str) -> tuple[int, int]:
    """(completedTasks, totalTasks) from `openspec list --json` - archive's own parser."""
    code, data, stderr = openspec_json(project_dir, "list", "--json")
    payload = fail_on(code, data, stderr, "openspec list")
    for entry in payload.get("changes") or []:
        if isinstance(entry, dict) and entry.get("name") == change:
            return int(entry.get("completedTasks") or 0), int(entry.get("totalTasks") or 0)
    raise SDDError(f"change '{change}' not found among active changes (openspec list)")


def next_step(artifacts: list[dict], done: int, total: int) -> str:
    pending = [a for a in artifacts if a.get("status") != "done"]
    if pending:
        ready = next((a for a in pending if a.get("status") == "ready"), pending[0])
        return str(ready.get("id"))
    return "apply" if total == 0 or done < total else "archive"


def cmd_status(project_dir: Path, change: str) -> int:
    check_name(change)
    code, data, stderr = openspec_json(project_dir, "status", "--change", change, "--json")
    payload = fail_on(code, data, stderr, "openspec status")
    artifacts = [{"id": a.get("id"), "status": a.get("status")}
                 for a in payload.get("artifacts") or [] if isinstance(a, dict)]
    done, total = task_counts(project_dir, change)
    change_root = payload.get("changeRoot")
    emit({"change": change, "schema": payload.get("schemaName"), "artifacts": artifacts,
          "planning_complete": bool(payload.get("isPlanningComplete")),
          "tasks_total": total, "tasks_done": done,
          "next": next_step(artifacts, done, total),
          "change_dir_real": os.path.realpath(change_root) if change_root else None})
    return 0


# --------------------------------------------------------------------------- instructions

def cmd_instructions(project_dir: Path, artifact: str, change: str) -> int:
    check_name(change)
    code, data, stderr = openspec_json(project_dir, "instructions", artifact,
                                       "--change", change, "--json")
    emit(fail_on(code, data, stderr, f"openspec instructions {artifact}"))
    return 0


# --------------------------------------------------------------------------- archive

def cmd_archive(project_dir: Path, change: str, allow_incomplete: bool,
                reason: str | None) -> int:
    check_name(change)
    if allow_incomplete and not (reason and reason.strip()):
        raise SDDError("--allow-incomplete needs --reason (the user-confirmed reason)")
    done, total = task_counts(project_dir, change)
    # `archive -y` skips OpenSpec's own incomplete-task block, so this is the only guard.
    if not allow_incomplete:
        if total == 0:
            raise SDDError(f"'{change}' has no tasks in tasks.md; refusing to archive "
                           "(use --allow-incomplete --reason if the user confirms)")
        if done < total:
            raise SDDError(f"'{change}' has {total - done} of {total} task(s) incomplete; "
                           "refusing to archive (use --allow-incomplete --reason if the "
                           "user confirms)")

    report = validate_change(project_dir, change)
    if not report["valid"]:
        print_blocking(report)
        raise SDDError(f"'{change}' failed validation; not archived")

    code, data, stderr = openspec_json(project_dir, "archive", change, "-y", "--json")
    errors = status_errors(data)
    if errors:
        raise SDDError(f"openspec archive refused: {format_errors(errors)}")
    if data is None:
        detail = f": {stderr}" if stderr else ""
        raise SDDError(f"openspec archive printed no JSON (exit {code}); treating as "
                       f"failed{detail}")
    result = data.get("archive")
    if not isinstance(result, dict):
        raise SDDError(f"openspec archive reported no archive result (exit {code}); "
                       "treating as failed")
    if code != 0:
        raise SDDError(f"openspec archive exited {code}" + (f": {stderr}" if stderr else ""))
    path = result.get("path")
    emit({"change": change, "archived_as": result.get("archivedAs"), "path": path,
          "path_real": os.path.realpath(path) if path else None,
          "specs_updated": bool(result.get("specsUpdated")),
          "totals": result.get("totals") or {},
          "tasks_done": done, "tasks_total": total,
          "allow_incomplete": {"reason": reason} if allow_incomplete else None})
    return 0


# --------------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guarded wrapper around the OpenSpec CLI for the /sdd relay. Every "
                    "openspec call runs with OPENSPEC_TELEMETRY=0 and DO_NOT_TRACK=1, from "
                    "the real parent of a symlinked openspec/ (the md workstation).",
        epilog="Exit codes: 0 = success, 1 = error, 2 = no-op.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-dir", type=Path, default=Path("."),
                        help="Project root directory (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("preflight", parents=[common], help="Check openspec and git versions",
                   description="Print {openspec: {path, version, ok, min, pinned}, git: "
                               "{version, ok, min}, bmad, tea}. openspec is looked up on "
                               "PATH, then in node_modules/.bin. Exit 0 both ok; 1 openspec "
                               "missing or older than 1.13, or git older than 2.31 (the "
                               "install hint goes to stderr).")

    init = sub.add_parser("init", parents=[common], help="Initialise openspec/ for /sdd",
                          description="Run `openspec init --tools none` (config.yaml, "
                                      "specs/, changes/archive/ only; no /opsx commands or "
                                      "skills) when openspec/config.yaml is missing; set its "
                                      "default schema to avengers-sdd, and copy the plugin's "
                                      "avengers-sdd schema into openspec/schemas/. An "
                                      "existing openspec/ (or symlink into the md "
                                      "workstation) is extended and an existing config.yaml "
                                      "is kept. A dangling openspec symlink is refused. Exit "
                                      "0; 2 config.yaml and the schema already exist; 1 on "
                                      "error.")
    init.add_argument("--dry-run", action="store_true", help="Report without changing anything")

    new = sub.add_parser("new", parents=[common], help="Create a change pinned to a schema",
                         description="Run `openspec new change <change> --schema S --json`; "
                                     "the schema is pinned in the change's .openspec.yaml. "
                                     "Print {change, schema, path, change_dir_real}. Exit 0; "
                                     "1 invalid name, existing change, or other error.")
    new.add_argument("change", help="Change id (kebab-case)")
    new.add_argument("--schema", required=True,
                     help="Schema to pin: spec-driven (quick) or avengers-sdd (standard)")

    val = sub.add_parser("validate", parents=[common], help="Strict validation of a change",
                         description="Run `openspec validate <change> --strict --json` and "
                                     "also fail on the INFO issues 'Archive would refuse this "
                                     "delta' and 'Could not check archive merge conflicts'. "
                                     "Print {change, valid, openspec_valid, issues, "
                                     "blocking}. Exit 0 valid; 1 invalid or error.")
    val.add_argument("change", help="Change id")

    stat = sub.add_parser("status", parents=[common], help="Artifacts, tasks and next step",
                          description="Print {change, schema, artifacts, planning_complete, "
                                      "tasks_total, tasks_done, next, change_dir_real}. Task "
                                      "counts come from `openspec list --json`, the parser "
                                      "archive uses. next is the first unfinished artifact, "
                                      "else apply, else archive. change_dir_real is the "
                                      "realpath to hand to subagents. Exit 0; 1 on error.")
    stat.add_argument("change", help="Change id")

    ins = sub.add_parser("instructions", parents=[common],
                         help="OpenSpec's instructions for an artifact or apply",
                         description="Print `openspec instructions <artifact> --change "
                                     "<change> --json` unchanged (instruction, template, "
                                     "resolvedOutputPath, dependencies; for apply: "
                                     "contextFiles, tasks, progress), so the relay never "
                                     "calls openspec without the telemetry opt-out. Exit 0; "
                                     "1 on error.")
    ins.add_argument("artifact", help="Artifact id (proposal, specs, design, tests, tasks) "
                                      "or apply")
    ins.add_argument("change", help="Change id")

    arc = sub.add_parser("archive", parents=[common], help="Guarded archive of a change",
                         description="Refuse when tasks.md has no tasks or any is "
                                     "incomplete, then run validate (as above), then "
                                     "`openspec archive <change> -y --json`. Empty output, "
                                     "`archive: null`, or a status[] error is a failure "
                                     "(code/message/fix on stderr). Print {change, "
                                     "archived_as, path, path_real, specs_updated, totals, "
                                     "tasks_done, tasks_total, allow_incomplete}. Exit 0 "
                                     "archived; 1 refused or error.")
    arc.add_argument("change", help="Change id")
    arc.add_argument("--allow-incomplete", action="store_true",
                     help="Archive despite missing or incomplete tasks (needs --reason)")
    arc.add_argument("--reason", help="User-confirmed reason for --allow-incomplete")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_dir = Path(os.path.normpath(args.project_dir.expanduser().absolute()))
    if not project_dir.is_dir():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 1
    try:
        if args.command == "preflight":
            return cmd_preflight(project_dir)
        if args.command == "init":
            return cmd_init(project_dir, args.dry_run)
        if args.command == "new":
            return cmd_new(project_dir, args.change, args.schema)
        if args.command == "validate":
            return cmd_validate(project_dir, args.change)
        if args.command == "status":
            return cmd_status(project_dir, args.change)
        if args.command == "instructions":
            return cmd_instructions(project_dir, args.artifact, args.change)
        return cmd_archive(project_dir, args.change, args.allow_incomplete, args.reason)
    except (SDDError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
