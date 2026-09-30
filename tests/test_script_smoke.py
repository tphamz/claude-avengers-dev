"""Smoke test: every bundled script runs `--help` cleanly (stdlib unittest).

Catches import-time and syntax errors (for example a `-> Path | None` annotation
without `from __future__ import annotations` on Python 3.9) in scripts that no
other test imports. Runs each script with the current interpreter, so the CI
matrix covers every supported Python.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bundled_scripts() -> list[Path]:
    """skills/*/scripts/*.py plus tools/*.py, sorted for stable subtest order."""
    return sorted([*ROOT.glob("skills/*/scripts/*.py"), *ROOT.glob("tools/*.py")])


class ScriptHelpSmokeTests(unittest.TestCase):
    def test_scripts_found(self) -> None:
        self.assertTrue(bundled_scripts(), f"no scripts found under {ROOT / 'skills'}")

    def test_every_script_prints_help(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_CONFIG_NOSYSTEM": "1"}
            for script in bundled_scripts():
                rel = script.relative_to(ROOT)
                with self.subTest(script=str(rel)):
                    proc = subprocess.run([sys.executable, str(script), "--help"],
                                          cwd=home, env=env, capture_output=True,
                                          text=True, timeout=60, check=False)
                    self.assertEqual(proc.returncode, 0,
                                     f"{rel}: `--help` exited {proc.returncode}, expected 0\n"
                                     f"stderr:\n{proc.stderr}")
                    self.assertTrue(proc.stdout.strip(),
                                    f"{rel}: `--help` printed nothing on stdout")


if __name__ == "__main__":
    unittest.main()
