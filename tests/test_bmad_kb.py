"""Tests for skills/bmad/scripts/bmad-kb.py (stdlib unittest).

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

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "bmad" / "scripts" / "bmad-kb.py"
_spec = importlib.util.spec_from_file_location("bmad_kb", SCRIPT)
bmad_kb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bmad_kb)

GIT_IDENTITY = ["-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]

# Isolate every git call (tests and the script under test) from user/system config.
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

BMM_CONFIG = 'project_knowledge: "{project-root}/docs"\noutput_folder: _bmad-output\n'


class ProjectCase(unittest.TestCase):
    """Base case: a temp project dir with helpers for files, git, and running the CLI."""

    def setUp(self) -> None:
        env_patch = mock.patch.dict(os.environ, GIT_ENV)
        env_patch.start()
        self.addCleanup(env_patch.stop)
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

    def test_rebased_away_stamp_is_stale(self) -> None:
        self.stamped_repo()
        self.write(".avengers/kb.json", json.dumps({"commit": "f" * 40}))
        report = self.status()
        self.assertEqual(report["state"], "stale")
        self.assertEqual([s["type"] for s in report["signals"]], ["unknown_stamp"])

    def test_avengers_and_bmad_changes_are_excluded(self) -> None:
        self.stamped_repo()
        files = {f".avengers/relay-sequences/bmad-{i}.yaml": "s\n" for i in range(12)}
        files.update({f"_bmad/bmm/agents/a_{i}.md": "a\n" for i in range(12)})
        files["_bmad/bmm/package.json"] = "{}\n"
        files["_bmad/migrations/0001.sql"] = "x\n"
        self.commit("chore: bmad update", files)
        self.assertEqual(self.status()["state"], "fresh")

    def test_non_ascii_kb_dir_is_excluded(self) -> None:
        self.init_repo()
        self.install_bmad('project_knowledge: "{project-root}/dócs"\noutput_folder: _bmad-output\n')
        self.write("dócs/index.md", "# index\n")
        self.commit("chore: init")
        self.assertEqual(self.run_cli("stamp")[0], 0)
        self.commit("docs: regen", {f"dócs/api_{i}.proto": "p\n" for i in range(25)})
        self.assertEqual(self.status()["state"], "fresh")

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores dir perms")
    def test_malformed_marker_backup_failure_is_error(self) -> None:
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.commit("chore: init")
        self.write(".avengers/kb.json", "{not json")
        avengers = self.root / ".avengers"
        avengers.chmod(0o500)
        try:
            code, _, err = self.run_cli("status")
        finally:
            avengers.chmod(0o700)
        self.assertEqual(code, 1)
        self.assertIn("cannot back it up", err)

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

    def test_non_ascii_paths_are_unquoted(self) -> None:
        self.base = self.commit("docs: add dir", {"dócs/readme.md": "r\n"})
        self.commit("feat: contract", {"dócs/api.proto": "syntax\n"})
        report = self.impact()
        self.assertEqual(report["signals"], [{"type": "api_contract", "detail": "dócs/api.proto"}])
        self.assertEqual(report["changed_areas"], ["dócs"])

    def test_non_ascii_new_top_level_dir(self) -> None:
        self.commit("feat: new area", {"módulo/main.py": "run\n"})
        self.assertIn({"type": "new_top_level_dir", "detail": "módulo/"}, self.impact()["signals"])

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


class MonorepoTests(ProjectCase):
    """The project dir is a subdirectory of the git repo."""

    def test_breaking_commit_outside_project_dir_is_ignored(self) -> None:
        self.init_repo()
        project = self.root / "apps" / "web"
        self.write("apps/web/_bmad/bmm/config.yaml", BMM_CONFIG)
        self.write("apps/web/src/app.py", "a\n")
        base = self.commit("chore: init")
        self.commit("feat!: other app breaks", {"apps/api/src/main.py": "x\n"})
        self.commit("fix: web typo", {"apps/web/src/app.py": "b\n"})
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bmad_kb.main(["impact", "--base", base, "--project-dir", str(project)])
        self.assertEqual(code, 0)
        report = json.loads(out.getvalue())
        self.assertFalse(report["refresh_recommended"])
        self.assertEqual(report["changed_areas"], ["src"])


class StampTests(ProjectCase):
    def setUp(self) -> None:
        super().setUp()
        self.init_repo()
        self.install_bmad()
        self.make_kb()
        self.head = self.commit("chore: init")
        self.marker = self.root / ".avengers" / "kb.json"
        self.branch = self.git("symbolic-ref", "--short", "HEAD")

    def entry(self, data: dict | None = None) -> dict:
        data = data or json.loads(self.marker.read_text(encoding="utf-8"))
        return data["branches"][self.branch]

    def test_write(self) -> None:
        code, _, _ = self.run_cli("stamp")
        self.assertEqual(code, 0)
        data = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 2)
        self.assertEqual(self.entry(data)["commit"], self.head)
        self.assertEqual(data["index_path"], "docs/index.md")
        self.assertEqual(data["context_path"], "_bmad-output/project-context.md")
        self.assertIn("stamped_at", self.entry(data))
        self.assertEqual(self.entry(data)["arch_hashes"], {})
        self.assertFalse((self.root / ".claude" / "rules" / "avengers-kb.md").exists())

    def test_dry_run_prints_without_writing(self) -> None:
        code, out, _ = self.run_cli("stamp", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(self.entry(json.loads(out))["commit"], self.head)
        self.assertFalse(self.marker.exists())

    def test_legacy_flat_marker_upgraded_in_place(self) -> None:
        self.write(".avengers/kb.json", json.dumps({"commit": "f" * 40}))
        self.assertEqual(self.run_cli("stamp")[0], 0)
        data = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertNotIn("commit", data)
        self.assertEqual(self.entry(data)["commit"], self.head)

    def test_detached_head_key(self) -> None:
        self.git("checkout", "-q", "--detach")
        self.assertEqual(self.run_cli("stamp")[0], 0)
        data = json.loads(self.marker.read_text(encoding="utf-8"))
        self.assertEqual(list(data["branches"]), [f"HEAD@{self.head[:7]}"])

    def test_already_stamped_is_noop(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        code, _, err = self.run_cli("stamp")
        self.assertEqual(code, 2)
        self.assertIn("no-op", err)

    def test_restamp_after_new_commit(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        new_head = self.commit("feat: more", {"src/b.py": "b\n"})
        self.assertEqual(self.run_cli("stamp")[0], 0)
        self.assertEqual(self.entry()["commit"], new_head)

    def test_non_git_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            # tempdirs are never inside a repo here; the ceiling makes that explicit
            os.environ["GIT_CEILING_DIRECTORIES"] = str(Path(other).resolve().parent)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = bmad_kb.main(["stamp", "--project-dir", other])
        self.assertEqual(code, 1)


class BranchTests(ProjectCase):
    """The marker is keyed per branch so worktrees on different branches coexist."""

    def setUp(self) -> None:
        super().setUp()
        self.write(".gitignore", ".avengers/\n")
        self.main_head = self.stamped_repo()
        self.main = self.git("symbolic-ref", "--short", "HEAD")
        self.marker = self.root / ".avengers" / "kb.json"

    def test_unstamped_branch_falls_back_to_newest(self) -> None:
        self.git("checkout", "-q", "-b", "feature")
        report = self.status()
        self.assertEqual(report["state"], "stale")
        self.assertEqual(report["branch"], "feature")
        self.assertEqual([s["type"] for s in report["signals"]], ["branch_unstamped"])
        self.assertEqual(report["stamped_commit"], self.main_head)

    def test_two_branches_do_not_overwrite(self) -> None:
        self.git("checkout", "-q", "-b", "feature")
        feature_head = self.commit("feat: x", {"src/x.py": "x\n"})
        self.assertEqual(self.run_cli("stamp")[0], 0)
        branches = json.loads(self.marker.read_text(encoding="utf-8"))["branches"]
        self.assertEqual(branches[self.main]["commit"], self.main_head)
        self.assertEqual(branches["feature"]["commit"], feature_head)
        self.git("checkout", "-q", self.main)
        report = self.status()
        self.assertEqual((report["state"], report["stamped_commit"]), ("fresh", self.main_head))


class WorkstationTests(ProjectCase):
    """KB marker and architecture signal with an md workstation behind _bmad-output."""

    def setUp(self) -> None:
        super().setUp()
        self._ws_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._ws_tmp.cleanup)
        self.ws = Path(self._ws_tmp.name).resolve() / "repo"
        (self.ws / "avengers").mkdir(parents=True)
        self.init_repo()
        self.install_bmad('project_knowledge: "{project-root}/_bmad-output/project-knowledge"\n'
                          'planning_artifacts: "{output_folder}/planning-artifacts"\n'
                          'output_folder: _bmad-output\n')
        (self.root / "_bmad-output").symlink_to(self.ws, target_is_directory=True)
        (self.root / ".git" / "info").mkdir(parents=True, exist_ok=True)
        (self.root / ".git" / "info" / "exclude").write_text("/_bmad-output\n")
        self.write(".avengers/settings.json", json.dumps({"mdWorkstation": str(self.ws)}))
        (self.ws / "project-knowledge").mkdir()
        (self.ws / "project-knowledge" / "index.md").write_text("# index\n")
        (self.ws / "project-context.md").write_text("# context\n")
        self.arch = self.ws / "planning-artifacts" / "architecture.md"
        self.arch.parent.mkdir()
        self.arch.write_text("# arch v1\n")
        self.write(".gitignore", ".avengers/\n")
        self.head = self.commit("chore: init")
        self.branch = self.git("symbolic-ref", "--short", "HEAD")
        self.ws_marker = self.ws / "avengers" / "kb.json"
        self.legacy = self.root / ".avengers" / "kb.json"

    def test_stamp_writes_workstation_marker_with_relative_paths(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        data = json.loads(self.ws_marker.read_text(encoding="utf-8"))
        self.assertEqual(data["index_path"], "project-knowledge/index.md")
        self.assertEqual(data["context_path"], "project-context.md")
        self.assertIn("planning-artifacts/architecture.md",
                      data["branches"][self.branch]["arch_hashes"])
        self.assertFalse(self.legacy.exists())
        report = self.status()
        self.assertEqual(report["state"], "fresh")
        self.assertEqual(report["workstation"], str(self.ws))
        self.assertEqual(report["marker_path"], str(self.ws_marker))

    def test_in_repo_path_is_project_root_relative(self) -> None:
        self.install_bmad('project_knowledge: "{project-root}/docs"\noutput_folder: _bmad-output\n')
        self.write("docs/index.md", "# index\n")
        self.assertEqual(self.run_cli("stamp")[0], 0)
        data = json.loads(self.ws_marker.read_text(encoding="utf-8"))
        self.assertEqual(data["index_path"], "{project-root}/docs/index.md")

    def test_legacy_marker_read_then_moved(self) -> None:
        self.write(".avengers/kb.json", json.dumps({"commit": self.head}))
        report = self.status()
        self.assertEqual((report["state"], report["marker_path"]), ("fresh", str(self.legacy)))
        self.commit("feat: more", {"src/b.py": "b\n"})
        code, out, _ = self.run_cli("stamp")
        self.assertEqual(code, 0)
        self.assertIn("Moved legacy", out)
        self.assertFalse(self.legacy.exists())
        self.assertTrue(self.ws_marker.exists())

    def test_architecture_hash_signal_without_commit(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        self.arch.write_text("# arch v2\n")
        report = self.status()
        self.assertEqual(report["state"], "stale")
        self.assertEqual(report["signals"], [{
            "type": "architecture",
            "detail": "planning-artifacts/architecture.md (content changed)"}])
        self.assertEqual(self.run_cli("stamp")[0], 0)
        self.assertEqual(self.status()["state"], "fresh")
        self.assertEqual(self.run_cli("stamp")[0], 2)

    def test_architecture_hash_signal_in_impact(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        (self.ws / "planning-artifacts" / "architecture-v2.md").write_text("# new\n")
        self.commit("fix: typo", {"src/a.py": "a\n"})
        code, out, _ = self.run_cli("impact", "--base", self.head)
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertTrue(report["refresh_recommended"])
        self.assertIn({"type": "architecture",
                       "detail": "planning-artifacts/architecture-v2.md (added)"},
                      report["signals"])

    def test_stamp_refreshes_kb_rules_file(self) -> None:
        self.assertEqual(self.run_cli("stamp")[0], 0)
        rules = self.root / ".claude" / "rules" / "avengers-kb.md"
        lines = rules.read_text(encoding="utf-8").splitlines()
        expected = f"@{self.ws / 'project-context.md'}"
        self.assertIn(expected, lines)
        self.assertIn("`grep -R` / `find -L`", rules.read_text(encoding="utf-8"))
        # A moved workstation replaces the stale import instead of adding a second one.
        rules.write_text(rules.read_text().replace(expected, "@/old/ws/project-context.md"))
        self.commit("feat: c", {"src/c.py": "c\n"})
        self.assertEqual(self.run_cli("stamp")[0], 0)
        lines = rules.read_text(encoding="utf-8").splitlines()
        self.assertIn(expected, lines)
        self.assertNotIn("@/old/ws/project-context.md", lines)

    def test_missing_workstation_falls_back_to_legacy_location(self) -> None:
        self.write(".avengers/settings.json", json.dumps({"mdWorkstation": "/nonexistent/ws"}))
        code, _, err = self.run_cli("stamp")
        self.assertEqual(code, 0)
        self.assertIn("not found", err)
        self.assertTrue(self.legacy.exists())


class CliHelpTests(unittest.TestCase):
    def test_help_for_each_subcommand(self) -> None:
        for argv in ([], ["preflight"], ["status"], ["impact"], ["stamp"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, str(SCRIPT), *argv, "--help"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage", proc.stdout)


if __name__ == "__main__":
    unittest.main()
