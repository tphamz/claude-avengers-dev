#!/usr/bin/env python3
"""
make-debug-fixture.py - Build a throwaway project for `claude --debug` skill sessions.

Dev-only tooling; not part of the plugin surface. Creates, under --dest:

  md-root/     a dedicated md git repo (the md root for the workstation flows)
  remote.git/  a bare repo, added to app as the remote `local` for push experiments
  app/         a git repo with a tiny Python module and test; origin is the fake
               git@github.com:fixture/app.git, so the workstation name is app-mds
  app-wt/      a second worktree of app (same remote key as app)
  home/        a scratch HOME for running workstation.py / openspec by hand;
               `claude` itself runs with the real HOME so the login is kept
  .avengers-debug-fixture   marker; --force deletes only directories that carry it

Prints the commands to run next. Never runs npm, npx, or claude, and never
touches the real HOME.

Exit codes:
  0 = fixture created
  1 = error (git failure, --dest is a symlink, or --force refused)
  2 = no-op (--dest exists and --force was not given)
"""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = ".avengers-debug-fixture"
FAKE_ORIGIN = "git@github.com:fixture/app.git"
GIT_IDENTITY = ["-c", "user.name=Avengers Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
                "-c", "init.defaultBranch=main"]

APP_FILES = {
    "README.md": "# app\n\nFixture project for avengers-dev debug sessions.\n",
    "app/__init__.py": "",
    "app/greet.py": 'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n',
    "tests/__init__.py": "",
    "tests/test_greet.py": (
        "import unittest\n\nfrom app.greet import greet\n\n\n"
        "class GreetTests(unittest.TestCase):\n"
        "    def test_greet(self) -> None:\n"
        '        self.assertEqual(greet("Tony"), "Hello, Tony!")\n\n\n'
        'if __name__ == "__main__":\n    unittest.main()\n'
    ),
}


class FixtureError(Exception):
    """A failure reported on stderr with exit code 1."""


def git_env() -> dict[str, str]:
    """Ignore the user's global and system git config (hooks, signing, templates)."""
    return {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *GIT_IDENTITY, *args], cwd=cwd, env=git_env(),
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise FixtureError(f"git {' '.join(args)} failed in {cwd}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def write_files(base: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def is_same_or_ancestor(path: Path, other: Path) -> bool:
    """True when path == other or path is a parent of other."""
    return path == other or path in other.parents


def check_force_target(dest: Path) -> None:
    """Refuse to delete anything that is not a fixture this tool wrote."""
    home = Path(os.path.realpath(Path.home()))
    protected = {
        "the current directory or its ancestors": Path(os.path.realpath(Path.cwd())),
        "HOME or its ancestors": home,
        "the avengers-dev repo or its ancestors": Path(os.path.realpath(REPO_ROOT)),
    }
    if dest == Path(dest.anchor):
        raise FixtureError(f"refusing --force on {dest}: filesystem root")
    for what, path in protected.items():
        if is_same_or_ancestor(dest, path):
            raise FixtureError(f"refusing --force on {dest}: it is {what} ({path})")
    if not dest.is_dir():
        raise FixtureError(f"refusing --force on {dest}: not a directory")
    if not (dest / MARKER).is_file():
        raise FixtureError(f"refusing --force on {dest}: no {MARKER} marker, so this tool "
                           f"did not create it")


def build(dest: Path) -> None:
    dest.mkdir(parents=True)
    (dest / MARKER).write_text("Created by avengers-dev tools/make-debug-fixture.py\n",
                               encoding="utf-8")

    md_root = dest / "md-root"
    md_root.mkdir()
    git(md_root, "init", "-q")
    write_files(md_root, {"README.md": "# md-root\n\nDedicated md repo for workstations.\n"})
    git(md_root, "add", "README.md")
    git(md_root, "commit", "-q", "-m", "chore: init md root")

    remote = dest / "remote.git"
    git(dest, "init", "-q", "--bare", str(remote))

    app = dest / "app"
    app.mkdir()
    git(app, "init", "-q")
    write_files(app, APP_FILES)
    git(app, "add", "--", *APP_FILES)
    git(app, "commit", "-q", "-m", "feat: greet module with a test")
    git(app, "remote", "add", "origin", FAKE_ORIGIN)
    git(app, "remote", "add", "local", str(remote))
    git(app, "push", "-q", "local", "HEAD:refs/heads/main")
    git(app, "worktree", "add", "-q", "-b", "wt-second", str(dest / "app-wt"))

    home = dest / "home"
    for sub in (".config", ".local/share", ".cache"):
        (home / sub).mkdir(parents=True)


def next_steps(dest: Path) -> str:
    q = shlex.quote
    home = dest / "home"
    ws = REPO_ROOT / "skills" / "avengers-workstation" / "scripts" / "workstation.py"
    env = " ".join(f"{k}={q(str(v))}" for k, v in (
        ("HOME", home), ("XDG_CONFIG_HOME", home / ".config"),
        ("XDG_DATA_HOME", home / ".local" / "share"), ("XDG_CACHE_HOME", home / ".cache")))
    return "\n".join([
        f"Fixture ready: {dest}",
        "",
        "# Shell A - isolated HOME, for running workstation.py / openspec by hand only.",
        "# Do not start claude here: it would not find your login.",
        f"export {env}",
        f"python3 {q(str(ws))} resolve --project-dir {q(str(dest / 'app'))}",
        f"python3 {q(str(ws))} resolve --project-dir {q(str(dest / 'app-wt'))}",
        "",
        "# Hints only - this tool does not run them:",
        f"#   (cd {q(str(dest / 'app'))} && npx bmad-method install)",
        "#   npm i -g @fission-ai/openspec@latest",
        "",
        "# Shell B - your real HOME (keeps the claude login). Skills run here write",
        "# the workstation registry to your real ~/.avengers/.",
        f"cd {q(str(dest / 'app'))}",
        f"claude --debug --plugin-dir {q(str(REPO_ROOT))}",
        "",
        f"# md root for the workstation flows: {dest / 'md-root'}",
        f"# second worktree: {dest / 'app-wt'}",
        "# checklist: TESTING.md, 'Debug-session checklist'",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a throwaway project (md root, app repo + worktree, bare remote, "
                    "scratch HOME) for claude --debug skill sessions. Dev-only. "
                    "Exit 0 = created, 1 = error, 2 = --dest exists (use --force).")
    parser.add_argument("--dest", required=True, type=Path,
                        help="directory to create; must not exist unless --force")
    parser.add_argument("--force", action="store_true",
                        help=f"replace --dest, only if it holds the {MARKER} marker")
    args = parser.parse_args(argv)

    given = args.dest.expanduser()
    if given.is_symlink():
        print(f"make-debug-fixture: refusing --dest {given}: it is a symlink; pass the "
              f"real directory path", file=sys.stderr)
        return 1
    dest = Path(os.path.realpath(given))
    try:
        if dest.exists() or dest.is_symlink():
            if not args.force:
                print(f"{dest} already exists; pass --force to replace a fixture",
                      file=sys.stderr)
                return 2
            check_force_target(dest)
            shutil.rmtree(dest)
        build(dest)
    except FixtureError as exc:
        print(f"make-debug-fixture: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"make-debug-fixture: {exc}", file=sys.stderr)
        return 1
    print(next_steps(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
