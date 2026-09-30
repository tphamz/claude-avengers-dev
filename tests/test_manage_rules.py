"""Tests for skills/avengers-init/scripts/manage-rules.py (bare @path imports).

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "avengers-init" / "scripts"
          / "manage-rules.py")


class BareIncludeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.rules = Path(self._tmp.name) / ".claude" / "rules" / "avengers-kb.md"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args, "--rules-file",
                               str(self.rules)], capture_output=True, text=True, check=False)

    def test_bare_add_writes_at_path_with_header(self) -> None:
        proc = self.run_cli("add-include", "--bare", "--include-path", "/ws/project-context.md",
                            "--header", "# KB")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.rules.read_text(), "# KB\n\n@/ws/project-context.md\n")
        again = self.run_cli("add-include", "--bare", "--include-path", "/ws/project-context.md")
        self.assertEqual(again.returncode, 2)

    def test_bare_remove(self) -> None:
        self.run_cli("add-include", "--bare", "--include-path", "/ws/project-context.md")
        proc = self.run_cli("remove-include", "--bare", "--include-path",
                            "/ws/project-context.md")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("@/ws/project-context.md", self.rules.read_text())

    def test_default_form_unchanged(self) -> None:
        proc = self.run_cli("add-include", "--include-path", "/p/persona.md")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.rules.read_text(),
                         "# Avengers Dev - Active Rules\n\n@include /p/persona.md\n")


if __name__ == "__main__":
    unittest.main()
