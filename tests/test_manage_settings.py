"""Tests for skills/avengers-init/scripts/manage-settings.py list operations.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "avengers-init" / "scripts"
          / "manage-settings.py")

KEY = "permissions.additionalDirectories"


class ListOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.settings = Path(self._tmp.name) / ".claude" / "settings.local.json"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--settings-file", str(self.settings), *args],
            capture_output=True, text=True, check=False)

    def seed(self, data: dict) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text(json.dumps(data))

    def load(self) -> dict:
        return json.loads(self.settings.read_text())

    def test_add_creates_nested_list(self) -> None:
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/ws/a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.load(), {"permissions": {"additionalDirectories": ["/ws/a"]}})

    def test_add_keeps_siblings_and_order(self) -> None:
        self.seed({"env": {"X": "1"},
                   "permissions": {"allow": ["Bash(ls)"], "deny": ["Bash(rm)"],
                                   "additionalDirectories": ["/first"]}})
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/second")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = self.load()
        self.assertEqual(data["env"], {"X": "1"})
        self.assertEqual(data["permissions"]["allow"], ["Bash(ls)"])
        self.assertEqual(data["permissions"]["deny"], ["Bash(rm)"])
        self.assertEqual(data["permissions"]["additionalDirectories"], ["/first", "/second"])

    def test_add_duplicate_is_noop(self) -> None:
        self.seed({"permissions": {"additionalDirectories": ["/ws/a"]}})
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/ws/a")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.load()["permissions"]["additionalDirectories"], ["/ws/a"])

    def test_add_dry_run_prints_without_writing(self) -> None:
        self.seed({"permissions": {"allow": ["Bash(ls)"]}})
        before = self.settings.read_text()
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/ws/a", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        printed = json.loads(proc.stdout)
        self.assertEqual(printed["permissions"],
                         {"allow": ["Bash(ls)"], "additionalDirectories": ["/ws/a"]})
        self.assertEqual(self.settings.read_text(), before)

    def test_top_level_dry_run_flag_also_works(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--settings-file", str(self.settings), "--dry-run",
             "list-add", "--key", KEY, "--value", "/ws/a"],
            capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.settings.exists())

    def test_add_to_non_list_is_error(self) -> None:
        self.seed({"permissions": {"additionalDirectories": "/oops"}})
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/ws/a")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not a list", proc.stderr)

    def test_remove_keeps_siblings(self) -> None:
        self.seed({"permissions": {"allow": ["Bash(ls)"],
                                   "additionalDirectories": ["/a", "/b", "/c"]}})
        proc = self.run_cli("list-remove", "--key", KEY, "--value", "/b")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.load(), {"permissions": {"allow": ["Bash(ls)"],
                                                       "additionalDirectories": ["/a", "/c"]}})

    def test_remove_last_prunes_empty_containers_only(self) -> None:
        self.seed({"permissions": {"additionalDirectories": ["/a"]}, "env": {"X": "1"}})
        proc = self.run_cli("list-remove", "--key", KEY, "--value", "/a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.load(), {"env": {"X": "1"}})

    def test_remove_last_keeps_non_empty_parent(self) -> None:
        self.seed({"permissions": {"allow": ["Bash(ls)"], "additionalDirectories": ["/a"]}})
        self.assertEqual(self.run_cli("list-remove", "--key", KEY, "--value", "/a").returncode, 0)
        self.assertEqual(self.load(), {"permissions": {"allow": ["Bash(ls)"]}})

    def test_remove_absent_is_noop(self) -> None:
        self.seed({"permissions": {"allow": ["Bash(ls)"]}})
        self.assertEqual(self.run_cli("list-remove", "--key", KEY, "--value", "/a").returncode, 2)
        self.assertEqual(self.run_cli("list-remove", "--key", "nope.deeper",
                                      "--value", "/a").returncode, 2)

    def test_remove_dry_run_prints_without_writing(self) -> None:
        self.seed({"permissions": {"additionalDirectories": ["/a", "/b"]}})
        before = self.settings.read_text()
        proc = self.run_cli("list-remove", "--key", KEY, "--value", "/a", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["permissions"]["additionalDirectories"], ["/b"])
        self.assertEqual(self.settings.read_text(), before)

    def test_malformed_json_backed_up(self) -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text("{not json")
        proc = self.run_cli("list-add", "--key", KEY, "--value", "/a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(self.settings.with_suffix(".json.bak").exists())
        self.assertEqual(self.load(), {"permissions": {"additionalDirectories": ["/a"]}})

    def test_help_for_list_subcommands(self) -> None:
        for sub in ("list-add", "list-remove"):
            with self.subTest(sub=sub):
                proc = subprocess.run([sys.executable, str(SCRIPT), sub, "--help"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("--key", proc.stdout)


if __name__ == "__main__":
    unittest.main()
