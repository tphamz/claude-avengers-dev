#!/usr/bin/env python3
"""
pair-registry.py - the paired-reviewer registry and its SendMessage guard.

A paired builder team is one Thor and its own Captain that message each other and
IronMan (`main`) mid-run (`.claude/rules/ironman-delegation.md`, Paired Reviewers).
IronMan records each pair's agentIds here when it pairs them, and the plugin's
PreToolUse hook on SendMessage (scripts/sendmessage-guard.sh) runs `guard`, which
limits what a subagent may message.

The registry is project-local, at <project dir>/.avengers/pairs.json:
  {"version": 1,
   "pairs": {"<team>": {"thor": "<agentId>", "captain": "<agentId>"}}}
Either side may be absent while a pair is being set up (the Captain is dispatched
first, so its id is registered before its Thor's).

Commands:
  register --team T [--thor ID] [--captain ID]  - Add or update a team's agentIds
  unregister --team T                           - Remove a team (no-op if absent)
  list                                          - Print the registry as JSON
  guard                                         - PreToolUse hook: read the hook
                                                  payload on stdin, allow or deny
The project dir is --project-dir, else CLAUDE_PROJECT_DIR, else the current
directory. `guard` takes no --project-dir: it reads CLAUDE_PROJECT_DIR only, and
with that unset it treats the registry as missing.

`guard` restricts SUBAGENTS only. Claude Code puts `agent_id` in the PreToolUse
payload when the call fires inside a subagent or teammate; a main-session call has
none. `agent_type` alone is not a subagent signal (a `claude --agent <name>`
session sets it too), so the guard keys on `agent_id` only.
  - No `agent_id`: the main session (IronMan) - allowed, any target.
  - `agent_id` present: a target containing whitespace or `[` (a `name [ref]`,
    another session, a multi-word name) is denied first. Then a sender registered
    in a pair may message `main` and its own partner's agentId only; any other
    subagent may message `main` only.
For subagents it FAILS CLOSED: a missing, unreadable or malformed registry, an
unset CLAUDE_PROJECT_DIR, or a malformed `agent_id` leaves only `main`. A payload
that is not a JSON object cannot be attributed to the main session, so it is
denied.

Debugging: set AVENGERS_PAIR_GUARD_LOG=<file> to append one JSON line per guard
call with the payload's keys (never its values, apart from `agent_type`), to
confirm on a given Claude Code version which calls carry `agent_id`.

Exit codes:
  0 = success (guard: allowed)
  1 = error (bad arguments, unwritable registry)
  2 = guard: denied, with the reason on stderr
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterator

REGISTRY_REL = Path(".avengers") / "pairs.json"
# Held exclusively around every read-modify-write (register, unregister).
LOCK_REL = Path(".avengers") / "pairs.lock"
REGISTRY_VERSION = 1
IRONMAN_TARGET = "main"
GUARDED_TOOL = "SendMessage"
ROLES = ("thor", "captain")
# An agentId is one token: letters, digits, `-` and `_`. Anything with whitespace,
# `[`, `@`, `:` or `/` is a name, a ref or an address, never an id.
AGENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
TEAM_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
# A target with either of these is a `name [ref]` or a multi-word name.
FORBIDDEN_TARGET_CHARS = re.compile(r"[\s\[]")

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_DENY = 2


class RegistryError(Exception):
    """The registry exists but cannot be read or does not have the expected shape."""


# -- registry -------------------------------------------------------------------------------------

def registry_path(project_dir: Path) -> Path:
    return project_dir / REGISTRY_REL


def empty_registry() -> dict:
    return {"version": REGISTRY_VERSION, "pairs": {}}


def validate(data: object) -> dict:
    """Return the registry if every part has the expected shape, else raise."""
    if not isinstance(data, dict) or data.get("version") != REGISTRY_VERSION:
        raise RegistryError(f"expected an object with \"version\": {REGISTRY_VERSION}")
    pairs = data.get("pairs")
    if not isinstance(pairs, dict):
        raise RegistryError("\"pairs\" is not an object")
    for team, pair in pairs.items():
        if not TEAM_NAME.match(team):
            raise RegistryError(f"team name {team!r} is not valid")
        if not isinstance(pair, dict) or set(pair) - set(ROLES):
            raise RegistryError(f"team {team!r} must map only {list(ROLES)} to agentIds")
        for role, agent_id in pair.items():
            if not isinstance(agent_id, str) or not AGENT_ID.match(agent_id):
                raise RegistryError(f"team {team!r} {role} {agent_id!r} is not an agentId")
    return data


def load(project_dir: Path) -> dict:
    """The registry, or an empty one when the file does not exist. Raises RegistryError
    when it exists but is unreadable or malformed."""
    path = registry_path(project_dir)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty_registry()
    except (OSError, UnicodeDecodeError) as exc:
        raise RegistryError(f"{path}: {exc}") from exc
    try:
        return validate(json.loads(text))
    except json.JSONDecodeError as exc:
        raise RegistryError(f"{path}: not JSON ({exc})") from exc


@contextlib.contextmanager
def locked(project_dir: Path) -> Iterator[None]:
    """Hold an exclusive lock on .avengers/pairs.lock for a read-modify-write, so
    concurrent register and unregister calls cannot drop each other's changes.
    Readers (`list`, `guard`) need no lock: save() replaces the file atomically."""
    import fcntl  # POSIX only, like the plugin's bash hooks; imported here so --help loads anywhere

    lock_path = project_dir / LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def save(project_dir: Path, data: dict) -> Path:
    """Write the registry atomically (temp file in the same directory, then replace)."""
    path = registry_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".pairs.", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


def register(data: dict, team: str, ids: dict[str, str]) -> dict:
    """Add or update one team. An agentId may belong to one team only."""
    for role, agent_id in ids.items():
        owner = next((name for name, pair in data["pairs"].items()
                      if name != team and agent_id in pair.values()), None)
        if owner is not None:
            raise ValueError(f"{role} {agent_id} is already registered to team {owner}")
    data["pairs"].setdefault(team, {}).update(ids)
    return data


# -- guard ----------------------------------------------------------------------------------------

def partner_of(data: dict, sender: str) -> str | None:
    """The agentId paired with sender, or None when sender is unregistered or its
    partner is not registered yet."""
    for pair in data["pairs"].values():
        for role, agent_id in pair.items():
            if agent_id == sender:
                other = next(r for r in ROLES if r != role)
                return pair.get(other)
    return None


def decide(payload: object, project_dir: Path | None) -> tuple[bool, str]:
    """(allowed, reason) for one PreToolUse payload. Pure apart from reading the
    registry under project_dir; project_dir None means no registry."""
    if not isinstance(payload, dict):
        return False, "the hook payload is not a JSON object"
    if payload.get("tool_name") != GUARDED_TOOL:
        return True, f"not a {GUARDED_TOOL} call"
    if "agent_id" not in payload:
        return True, "a main-session call (no agent_id)"
    tool_input = payload.get("tool_input")
    target = tool_input.get("to") if isinstance(tool_input, dict) else None
    if not isinstance(target, str) or not target:
        return False, "the SendMessage call has no `to` target"
    if FORBIDDEN_TARGET_CHARS.search(target):
        return False, (f"target {target!r} contains whitespace or `[`: names, "
                       f"`name [ref]` targets and other sessions are never allowed")
    if target == IRONMAN_TARGET:
        return True, "IronMan (main)"
    sender = payload["agent_id"]
    if not isinstance(sender, str) or not AGENT_ID.match(sender):
        return False, "the sender's agent_id is malformed, so only `main` is allowed"
    if project_dir is None:
        return False, "CLAUDE_PROJECT_DIR is not set, so no pair registry can be read"
    try:
        data = load(project_dir)
    except RegistryError as exc:
        return False, f"the pair registry is unreadable ({exc})"
    partner = partner_of(data, sender)
    if partner is None:
        return False, (f"sender {sender} has no registered partner in "
                       f"{registry_path(project_dir)}, so only `main` is allowed")
    if target == partner:
        return True, "the sender's own registered partner"
    return False, f"target {target!r} is not the sender's registered partner"


def log_payload_keys(payload: object, log_path: str) -> None:
    """Append the payload's shape (keys only) to log_path; never fails the guard."""
    record = {"keys": sorted(payload) if isinstance(payload, dict) else None,
              "has_agent_id": isinstance(payload, dict) and "agent_id" in payload,
              "agent_type": payload.get("agent_type") if isinstance(payload, dict) else None}
    try:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass


def guard(stdin_text: str, env: dict[str, str]) -> int:
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError:
        payload = None
    if env.get("AVENGERS_PAIR_GUARD_LOG"):
        log_payload_keys(payload, env["AVENGERS_PAIR_GUARD_LOG"])
    project = env.get("CLAUDE_PROJECT_DIR") or None
    allowed, reason = decide(payload, Path(project) if project else None)
    if allowed:
        return EXIT_OK
    print(f"SendMessage denied: {reason}. A paired agent may message only IronMan "
          f"(`main`) and its own registered partner; escalate to `main` instead.",
          file=sys.stderr)
    return EXIT_DENY


# -- CLI ------------------------------------------------------------------------------------------

def agent_id_arg(value: str) -> str:
    if not AGENT_ID.match(value):
        raise argparse.ArgumentTypeError(f"{value!r} is not an agentId (letters, digits, - and _)")
    return value


def team_arg(value: str) -> str:
    if not TEAM_NAME.match(value):
        raise argparse.ArgumentTypeError(f"{value!r} is not a team name (letters, digits, . - _)")
    return value


def project_dir_of(args: argparse.Namespace) -> Path:
    return Path(args.project_dir or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pair-registry.py",
        description="Register paired Thor/Captain agentIds and guard SendMessage targets.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("register", "add or update a team's agentIds"),
                            ("unregister", "remove a team"),
                            ("list", "print the registry as JSON")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--project-dir", help="project directory holding .avengers/")
        if name != "list":
            cmd.add_argument("--team", required=True, type=team_arg, help="team label")
        if name == "register":
            cmd.add_argument("--thor", type=agent_id_arg, help="the team's Thor agentId")
            cmd.add_argument("--captain", type=agent_id_arg, help="the team's Captain agentId")
    sub.add_parser("guard", help="PreToolUse hook: read the payload on stdin; exit 2 denies")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "guard":
        return guard(sys.stdin.read(), dict(os.environ))
    project_dir = project_dir_of(args)
    ids = {role: getattr(args, role) for role in ROLES if getattr(args, role, None)}
    if args.command == "register" and not ids:
        print("register needs --thor, --captain or both", file=sys.stderr)
        return EXIT_ERROR
    try:
        if args.command == "list":
            data = load(project_dir)
        else:
            with locked(project_dir):
                data = load(project_dir)
                if args.command == "register":
                    save(project_dir, register(data, args.team, ids))
                elif data["pairs"].pop(args.team, None) is not None:
                    save(project_dir, data)
    except (RegistryError, ValueError, OSError) as exc:
        print(f"pair-registry: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(json.dumps(data, indent=2, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
