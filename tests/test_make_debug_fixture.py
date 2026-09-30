"""Tests for tools/make-debug-fixture.py (stdlib unittest).

Every test builds under a temp dir with HOME patched to a temp home; git runs with
GIT_CONFIG_GLOBAL=os.devnull and GIT_CONFIG_NOSYSTEM=1.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "make-debug-fixture.py"
_spec = importlib.util.spec_from_file_location("make_debug_fixture", SCRIPT)
fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixture)

WS_SCRIPT = ROOT / "skills" / "avengers-workstation" / "scripts" / "workstation.py"
_ws_spec = importlib.util.spec_from_file_location("workstation_for_fixture", WS_SCRIPT)
workstation = importlib.util.module_from_spec(_ws_spec)
_ws_spec.loader.exec_module(workstation)


class FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(os.path.realpath(self._tmp.name))
        self.home = self.base / "realhome"
        self.home.mkdir()
        env_patch = mock.patch.dict(os.environ, {
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.base),
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.dest = self.base / "fx"

    def run_tool(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = fixture.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def build(self) -> str:
        code, out, err = self.run_tool("--dest", str(self.dest))
        self.assertEqual(code, 0, err)
        return out

    def git(self, cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              check=True).stdout.strip()

    def resolve(self, project: Path) -> dict:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workstation.main(["resolve", "--project-dir", str(project)])
        self.assertEqual(code, 0, err.getvalue())
        return json.loads(out.getvalue())


class BuildTests(FixtureCase):
    def test_structure(self) -> None:
        out = self.build()
        for rel in ("md-root/.git", "remote.git/HEAD", "app/.git", "app/app/greet.py",
                    "app/tests/test_greet.py", "app-wt/.git", "home/.config",
                    fixture.MARKER):
            self.assertTrue((self.dest / rel).exists(), f"{self.dest / rel} missing")
        self.assertEqual(self.git(self.dest / "md-root", "log", "--format=%s"),
                         "chore: init md root")
        self.assertEqual(self.git(self.dest / "app", "remote", "get-url", "origin"),
                         fixture.FAKE_ORIGIN)
        self.assertEqual(self.git(self.dest / "app", "remote", "get-url", "local"),
                         str(self.dest / "remote.git"))
        self.assertTrue(self.git(self.dest / "remote.git", "rev-parse", "main"))
        self.assertEqual(self.git(self.dest / "app", "log", "--format=%an <%ae>"),
                         "Avengers Fixture <fixture@example.invalid>")
        self.assertIn(f"claude --debug --plugin-dir {ROOT}", out)
        self.assertIn("npx bmad-method install", out)
        self.assertEqual(list(self.home.iterdir()), [], "the tool wrote into HOME")

    def test_fixture_app_tests_pass(self) -> None:
        self.build()
        proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                               "-t", "."], cwd=self.dest / "app", capture_output=True,
                              text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_worktree_shares_remote_key(self) -> None:
        self.build()
        worktrees = self.git(self.dest / "app", "worktree", "list", "--porcelain")
        self.assertIn(f"worktree {self.dest / 'app-wt'}", worktrees)
        app, wt = self.resolve(self.dest / "app"), self.resolve(self.dest / "app-wt")
        self.assertEqual(app["remote_key"], "github.com/fixture/app")
        self.assertEqual(wt["remote_key"], app["remote_key"])
        self.assertEqual(app["repo_name"], "app")


class ExistingDestTests(FixtureCase):
    def test_refuses_existing_dir_without_force(self) -> None:
        self.dest.mkdir()
        code, out, err = self.run_tool("--dest", str(self.dest))
        self.assertEqual(code, 2)
        self.assertIn("--force", err)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_force_replaces_a_fixture(self) -> None:
        self.build()
        stray = self.dest / "stray.txt"
        stray.write_text("x")
        code, _, err = self.run_tool("--dest", str(self.dest), "--force")
        self.assertEqual(code, 0, err)
        self.assertFalse(stray.exists())
        self.assertTrue((self.dest / "app" / ".git").exists())

    def test_force_refuses_without_marker(self) -> None:
        self.dest.mkdir()
        keep = self.dest / "keep.txt"
        keep.write_text("precious")
        code, _, err = self.run_tool("--dest", str(self.dest), "--force")
        self.assertEqual(code, 1)
        self.assertIn(fixture.MARKER, err)
        self.assertTrue(keep.exists())

    def test_force_refuses_protected_paths_even_with_marker(self) -> None:
        cwd = self.base / "work" / "sub"
        cwd.mkdir(parents=True)
        (self.base / "work" / fixture.MARKER).write_text("")
        (self.home / fixture.MARKER).write_text("")
        with mock.patch.object(Path, "cwd", return_value=cwd):
            for target, reason in ((self.base / "work", "current directory"),
                                   (cwd, "current directory"),
                                   (self.home, "HOME"),
                                   (Path("/"), "root")):
                with self.subTest(target=str(target)):
                    code, _, err = self.run_tool("--dest", str(target), "--force")
                    self.assertEqual(code, 1, err)
                    self.assertIn(reason, err)
        self.assertTrue((self.base / "work" / fixture.MARKER).exists())
        self.assertTrue((self.home / fixture.MARKER).exists())

    def test_force_refuses_repo_root(self) -> None:
        code, _, err = self.run_tool("--dest", str(ROOT), "--force")
        self.assertEqual(code, 1)
        self.assertIn("refusing --force", err)
        self.assertTrue((ROOT / "tools" / "make-debug-fixture.py").exists())


if __name__ == "__main__":
    unittest.main()
