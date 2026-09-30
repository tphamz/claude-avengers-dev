"""Tests for skills/bmad/scripts/bmad-kb.py (stdlib unittest).

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "bmad" / "scripts" / "bmad-kb.py"
_spec = importlib.util.spec_from_file_location("bmad_kb", SCRIPT)
bmad_kb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bmad_kb)

GIT_IDENTITY = ["-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]

BMM_CONFIG = 'project_knowledge: "{project-root}/docs"\noutput_folder: _bmad-output\n'


class ProjectCase(unittest.TestCase):
    """Base case: a temp project dir with helpers for files, git, and running the CLI."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers ---------------------------------------------------------------

    def write(self, rel: str, content: str = "x\n") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def git(self, *args: str) -> str:
        proc = subprocess.run(["git", *GIT_IDENTITY, *args], cwd=self.root,
                              capture_output=True, text=True, check=True)
        return proc.stdout.strip()

    def commit(self, message: str, files: dict[str, str] | None = None) -> str:
        for rel, content in (files or {}).items():
            self.write(rel, content)
        self.git("add", "-A")
        self.git("commit", "--allow-empty", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def init_repo(self) -> None:
        self.git("init", "-q")

    def install_bmad(self, config: str = BMM_CONFIG, tea: bool = False) -> None:
        self.write("_bmad/bmm/config.yaml", config)
        if tea:
            self.write("_bmad/tea/config.yaml", "test_framework: playwright\n")

    def make_kb(self) -> None:
        self.write("docs/index.md", "# index\n")
        self.write("_bmad-output/project-context.md", "# context\n")

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bmad_kb.main([*args, "--project-dir", str(self.root)])
        return code, out.getvalue(), err.getvalue()

    def status(self) -> dict:
        code, out, _ = self.run_cli("status")
        self.assertEqual(code, 0)
        return json.loads(out)

    def stamped_repo(self) -> str:
        """A git repo with BMAD installed, a KB, and a stamp at HEAD."""
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.write("src/app.py", "print('hi')\n")
        head = self.commit("chore: initial")
        code, _, _ = self.run_cli("stamp")
        self.assertEqual(code, 0)
        return head


class ConfigTests(ProjectCase):
    def config(self) -> dict[str, Path]:
        with contextlib.redirect_stderr(io.StringIO()):
            return bmad_kb.read_bmad_config(self.root)

    def test_quoted_project_root_value(self) -> None:
        self.install_bmad()
        self.assertEqual(self.config()["project_knowledge"], self.root / "docs")

    def test_relative_output_folder(self) -> None:
        self.install_bmad()
        self.assertEqual(self.config()["output_folder"], self.root / "_bmad-output")

    def test_inline_comment_stripped(self) -> None:
        self.install_bmad("project_knowledge: knowledge  # where docs live\n"
                          "output_folder: 'out' # quoted with comment\n")
        cfg = self.config()
        self.assertEqual(cfg["project_knowledge"], self.root / "knowledge")
        self.assertEqual(cfg["output_folder"], self.root / "out")

    def test_core_fallback_for_missing_keys(self) -> None:
        self.write("_bmad/bmm/config.yaml", "project_knowledge: kb\n")
        self.write("_bmad/core/config.yaml", "output_folder: core-out\nproject_knowledge: ignored\n")
        cfg = self.config()
        self.assertEqual(cfg["project_knowledge"], self.root / "kb")
        self.assertEqual(cfg["output_folder"], self.root / "core-out")

    def test_missing_keys_use_defaults_with_warning(self) -> None:
        self.write("_bmad/bmm/config.yaml", "user_name: t\nnested:\n  project_knowledge: no\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            cfg = bmad_kb.read_bmad_config(self.root)
        self.assertEqual(cfg["project_knowledge"], self.root / "docs")
        self.assertEqual(cfg["output_folder"], self.root / "_bmad-output")
        self.assertIn("WARNING", err.getvalue())


class PreflightTests(ProjectCase):
    def test_present(self) -> None:
        self.install_bmad()
        code, out, _ = self.run_cli("preflight")
        self.assertEqual((code, out.strip()), (0, "BMAD_OK"))

    def test_missing(self) -> None:
        code, out, err = self.run_cli("preflight")
        self.assertEqual((code, out.strip()), (1, "BMAD_MISSING"))
        self.assertIn("npx bmad-method install", err)

    def test_full_track_without_tea(self) -> None:
        self.install_bmad()
        code, out, _ = self.run_cli("preflight", "--track", "full")
        self.assertEqual((code, out.strip()), (2, "TEA_MISSING"))

    def test_full_track_with_tea(self) -> None:
        self.install_bmad(tea=True)
        code, out, _ = self.run_cli("preflight", "--track", "full")
        self.assertEqual((code, out.strip()), (0, "BMAD_OK"))

    def test_standard_track_ignores_tea(self) -> None:
        self.install_bmad()
        code, _, _ = self.run_cli("preflight", "--track", "standard")
        self.assertEqual(code, 0)


class StatusTests(ProjectCase):
    def test_bmad_missing_is_error(self) -> None:
        code, _, err = self.run_cli("status")
        self.assertEqual(code, 1)
        self.assertIn("npx bmad-method install", err)

    def test_missing(self) -> None:
        self.init_repo()
        self.install_bmad()
        self.commit("chore: init")
        report = self.status()
        self.assertEqual(report["state"], "missing")
        self.assertEqual(report["index_path"], "docs/index.md")
        self.assertEqual(report["context_path"], "_bmad-output/project-context.md")

    def test_unstamped(self) -> None:
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.commit("chore: init")
        self.assertEqual(self.status()["state"], "unstamped")

    def test_fresh(self) -> None:
        head = self.stamped_repo()
        report = self.status()
        self.assertEqual(report["state"], "fresh")
        self.assertEqual(report["stamped_commit"], head)
        self.assertEqual(report["head"], head)
        self.assertEqual(report["commits_since"], 0)

    def test_small_change_stays_fresh(self) -> None:
        self.stamped_repo()
        self.commit("fix: typo", {"src/app.py": "print('hello')\n"})
        report = self.status()
        self.assertEqual(report["state"], "fresh")
        self.assertEqual(report["commits_since"], 1)

    def test_stale_via_signal(self) -> None:
        self.stamped_repo()
        self.commit("feat!: drop v1 api", {"src/app.py": "print('v2')\n"})
        report = self.status()
        self.assertEqual(report["state"], "stale")
        self.assertIn("breaking_change", [s["type"] for s in report["signals"]])

    def test_stale_via_file_threshold(self) -> None:
        self.stamped_repo()
        files = {f"src/mod_{i}.py": f"x = {i}\n" for i in range(bmad_kb.STALE_FILE_THRESHOLD)}
        self.commit("feat: many modules", files)
        report = self.status()
        self.assertEqual(report["state"], "stale")
        self.assertEqual([s["type"] for s in report["signals"]], ["volume"])

    def test_docs_and_output_only_changes_are_not_stale(self) -> None:
        self.stamped_repo()
        files = {f"docs/page_{i}.md": "p\n" for i in range(15)}
        files.update({f"_bmad-output/story_{i}.md": "s\n" for i in range(15)})
        files["_bmad-output/package.json"] = "{}\n"
        self.commit("docs: regenerate", files)
        self.assertEqual(self.status()["state"], "fresh")

    def test_non_git_is_unknown(self) -> None:
        self.install_bmad()
        self.make_kb()
        self.write(".avengers/kb.json", json.dumps({"commit": "abc123"}))
        self.assertEqual(self.status()["state"], "unknown")

    def test_malformed_marker_backed_up_and_unstamped(self) -> None:
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.commit("chore: init")
        self.write(".avengers/kb.json", "{not json")
        code, out, err = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["state"], "unstamped")
        self.assertIn("WARNING", err)
        self.assertTrue((self.root / ".avengers" / "kb.json.bak").exists())
        self.assertFalse((self.root / ".avengers" / "kb.json").exists())


class ImpactTests(ProjectCase):
    def setUp(self) -> None:
        super().setUp()
        self.base = self.stamped_repo()

    def impact(self) -> dict:
        code, out, _ = self.run_cli("impact", "--base", self.base)
        self.assertEqual(code, 0)
        return json.loads(out)

    def signal_types(self, report: dict) -> list[str]:
        return [s["type"] for s in report["signals"]]

    def test_breaking_subject(self) -> None:
        self.commit("feat!: new auth", {"src/app.py": "auth\n"})
        report = self.impact()
        self.assertTrue(report["refresh_recommended"])
        self.assertIn("breaking_change", self.signal_types(report))

    def test_breaking_scoped_subject(self) -> None:
        self.commit("refactor(api)!: rename", {"src/app.py": "rename\n"})
        self.assertIn("breaking_change", self.signal_types(self.impact()))

    def test_breaking_change_body(self) -> None:
        self.commit("feat: new auth\n\nBREAKING CHANGE: tokens rotate", {"src/app.py": "a\n"})
        self.assertIn("breaking_change", self.signal_types(self.impact()))

    def test_package_json_change(self) -> None:
        self.commit("chore: deps", {"package.json": '{"name": "x"}\n'})
        report = self.impact()
        self.assertTrue(report["refresh_recommended"])
        self.assertIn({"type": "dependencies", "detail": "package.json"}, report["signals"])

    def test_migration(self) -> None:
        self.commit("feat: add column", {"src/db/migrations/0002_add.sql": "ALTER\n"})
        self.assertIn("migration", self.signal_types(self.impact()))

    def test_api_contract(self) -> None:
        self.commit("feat: spec", {"src/api/openapi.yaml": "openapi: 3.1\n"})
        self.assertIn("api_contract", self.signal_types(self.impact()))

    def test_architecture_doc_in_output_folder(self) -> None:
        self.commit("docs: arch", {"_bmad-output/planning/architecture.md": "# arch\n"})
        self.assertIn("architecture", self.signal_types(self.impact()))

    def test_new_top_level_dir(self) -> None:
        self.commit("feat: worker", {"worker/main.py": "run\n"})
        report = self.impact()
        self.assertIn({"type": "new_top_level_dir", "detail": "worker/"}, report["signals"])
        self.assertEqual(report["changed_areas"], ["worker"])

    def test_plain_fix_not_recommended(self) -> None:
        self.commit("fix: off by one", {"src/app.py": "fixed\n"})
        report = self.impact()
        self.assertFalse(report["refresh_recommended"])
        self.assertEqual(report["signals"], [])
        self.assertEqual(report["changed_areas"], ["src"])

    def test_no_commits_is_noop(self) -> None:
        code, out, _ = self.run_cli("impact", "--base", self.base)
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out)["refresh_recommended"])

    def test_bad_sha_is_error(self) -> None:
        code, _, err = self.run_cli("impact", "--base", "deadbeefdeadbeef")
        self.assertEqual(code, 1)
        self.assertIn("unknown commit", err)


class StampTests(ProjectCase):
    def setUp(self) -> None:
        super().setUp()
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.head = self.commit("chore: init")
        self.marker = self.root / ".avengers" / "kb.json"

    def test_write(self) -> None:
        code, _, _ = self.run_cli("stamp")
        self.assertEqual(code, 0)
        data = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual(data["commit"], self.head)
        self.assertEqual(data["index_path"], "docs/index.md")
        self.assertEqual(data["context_path"], "_bmad-output/project-context.md")
        self.assertIn("stamped_at", data)

    def test_dry_run_prints_without_writing(self) -> None:
        code, out, _ = self.run_cli("stamp", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["commit"], self.head)
        self.assertFalse(self.marker.exists())

    def test_already_stamped_is_noop(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        code, _, err = self.run_cli("stamp")
        self.assertEqual(code, 2)
        self.assertIn("no-op", err)

    def test_restamp_after_new_commit(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        new_head = self.commit("feat: more", {"src/b.py": "b\n"})
        self.assertEqual(self.run_cli("stamp")[0], 0)
        self.assertEqual(json.loads(self.marker.read_text(encoding="utf-8"))["commit"], new_head)

    def test_non_git_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = bmad_kb.main(["stamp", "--project-dir", other])
        self.assertEqual(code, 1)


class CliHelpTests(unittest.TestCase):
    def test_help_for_each_subcommand(self) -> None:
        for argv in ([], ["preflight"], ["status"], ["impact"], ["stamp"]):
            with self.subTest(argv=argv):
                proc = subprocess.run(["python3", str(SCRIPT), *argv, "--help"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage", proc.stdout)


if __name__ == "__main__":
    unittest.main()
