"""Tests for skills/sdd/scripts/sdd-openspec.py (stdlib unittest).

A fake `openspec` executable on PATH (a temp dir) prints canned output per
subcommand and records its argv and telemetry env. HOME is patched to a temp dir.

The integration test at the end runs the real CLI and is skipped unless OPENSPEC_BIN
points at an `openspec` binary; it isolates HOME and XDG_CONFIG_HOME itself.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "sdd" / "scripts" / "sdd-openspec.py"
_spec = importlib.util.spec_from_file_location("sdd_openspec", SCRIPT)
sdd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdd)

WS_SCRIPT = ROOT / "skills" / "avengers-workstation" / "scripts" / "workstation.py"
_ws_spec = importlib.util.spec_from_file_location("workstation_for_sdd", WS_SCRIPT)
workstation = importlib.util.module_from_spec(_ws_spec)
_ws_spec.loader.exec_module(workstation)

GIT_IDENTITY = ["-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]

FAKE_OPENSPEC = """#!{python}
import json, os, sys
from pathlib import Path

argv = sys.argv[1:]
with open(os.environ["FAKE_OPENSPEC_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"argv": argv, "cwd": os.getcwd(), "env": {{
        k: os.environ.get(k) for k in ("OPENSPEC_TELEMETRY", "DO_NOT_TRACK")}}}}) + "\\n")
scenario = json.loads(Path(os.environ["FAKE_OPENSPEC_SCENARIO"]).read_text(encoding="utf-8"))
key = argv[0] if argv else ""
if key == "init" and scenario.get("init_writes", True):
    root = Path("openspec")
    (root / "specs").mkdir(parents=True, exist_ok=True)
    (root / "changes" / "archive").mkdir(parents=True, exist_ok=True)
    config = root / "config.yaml"
    if not config.exists():
        config.write_text("schema: spec-driven\\n\\n# Project context (optional)\\n",
                          encoding="utf-8")
response = scenario.get(key, {{}})
sys.stdout.write(response.get("stdout", ""))
sys.stderr.write(response.get("stderr", ""))
sys.exit(response.get("exit", 0))
"""


def js(data: object) -> str:
    return json.dumps(data)


def list_json(name: str = "add-x", done: int = 2, total: int = 2) -> str:
    return js({"changes": [{"name": name, "completedTasks": done, "totalTasks": total,
                            "status": "in-progress"}], "root": {"path": "/p"}})


def validate_json(name: str = "add-x", valid: bool = True, issues: list | None = None) -> str:
    return js({"items": [{"id": name, "type": "change", "valid": valid,
                          "issues": issues or []}], "summary": {}, "version": "1.0"})


ARCHIVE_OK = js({"archive": {"change": "add-x", "archivedAs": "2026-01-01-add-x",
                             "path": "/tmp/openspec/changes/archive/2026-01-01-add-x",
                             "specsUpdated": True,
                             "totals": {"added": 1, "modified": 0, "removed": 0,
                                        "renamed": 0}},
                 "root": {"path": "/p"}})


class FakeCase(unittest.TestCase):
    """A temp project, a temp HOME, and a fake openspec first on PATH."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.project = self.base / "project"
        self.project.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.fake = self.bin / "openspec"
        self.fake.write_text(FAKE_OPENSPEC.format(python=sys.executable), encoding="utf-8")
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.log = self.base / "calls.jsonl"
        self.scenario_file = self.base / "scenario.json"
        self.scenario({"--version": {"stdout": "1.13.2\n"}})
        env_patch = mock.patch.dict(os.environ, {
            "HOME": str(self.home),
            "PATH": str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
            "FAKE_OPENSPEC_LOG": str(self.log),
            "FAKE_OPENSPEC_SCENARIO": str(self.scenario_file),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "OPENSPEC_TELEMETRY": "1",  # the wrapper must override this
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def record_ws(self, ws: Path) -> None:
        """Record ws as mdWorkstation, as `workstation.py set` does."""
        settings = self.project / ".avengers" / "settings.json"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"mdWorkstation": str(ws)}), encoding="utf-8")

    def scenario(self, data: dict) -> None:
        self.scenario_file.write_text(json.dumps(data), encoding="utf-8")

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines() if line]

    def subcommands(self) -> list[str]:
        return [call["argv"][0] for call in self.calls()]

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sdd.main([*args, "--project-dir", str(self.project)])
        return code, out.getvalue(), err.getvalue()


class PreflightTests(FakeCase):
    def test_ok(self) -> None:
        code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report["openspec"]["path"], str(self.fake))
        self.assertEqual(report["openspec"]["version"], "1.13.2")
        self.assertTrue(report["openspec"]["ok"])
        self.assertTrue(report["git"]["ok"])
        self.assertEqual((report["bmad"], report["tea"]), (False, False))

    def test_version_below_minimum(self) -> None:
        self.scenario({"--version": {"stdout": "1.12.9\n"}})
        code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["openspec"]["ok"])
        self.assertIn("npm i -g @fission-ai/openspec@latest", err)

    def test_version_with_prefix(self) -> None:
        self.scenario({"--version": {"stdout": "openspec v1.14.0\n"}})
        code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["openspec"]["version"], "1.14.0")

    def test_missing(self) -> None:
        empty = self.base / "empty"
        empty.mkdir()
        git_dir = str(Path(shutil.which("git")).parent)
        with mock.patch.dict(os.environ, {"PATH": str(empty) + os.pathsep + git_dir}):
            code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertIsNone(report["openspec"]["path"])
        self.assertFalse(report["openspec"]["ok"])
        self.assertIn("npm i -g @fission-ai/openspec@latest", err)

    def test_node_modules_fallback(self) -> None:
        local = self.project / "node_modules" / ".bin" / "openspec"
        local.parent.mkdir(parents=True)
        shutil.copy2(self.fake, local)
        git_dir = str(Path(shutil.which("git")).parent)
        with mock.patch.dict(os.environ, {"PATH": git_dir}):
            code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["openspec"]["path"], str(local))

    def test_old_git_fails(self) -> None:
        with mock.patch.object(sdd, "MIN_GIT", (99, 0)):
            code, out, err = self.run_cli("preflight")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["git"]["ok"])
        self.assertIn("git 99.0", err)

    def test_bmad_and_tea_flags(self) -> None:
        (self.project / "_bmad" / "tea").mkdir(parents=True)
        report = json.loads(self.run_cli("preflight")[1])
        self.assertEqual((report["bmad"], report["tea"]), (True, True))


class InitTests(FakeCase):
    def schema_dir(self, root: Path | None = None) -> Path:
        return (root or self.project / "openspec") / "schemas" / "avengers-sdd"

    def test_fresh_init_uses_tools_none_and_installs_schema(self) -> None:
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        init_calls = [c for c in self.calls() if c["argv"][0] == "init"]
        self.assertEqual([c["argv"] for c in init_calls],
                         [["init", "--tools", "none", "--no-animation"]])
        self.assertEqual(os.path.realpath(init_calls[0]["cwd"]), os.path.realpath(self.project))
        self.assertTrue((self.project / "openspec" / "changes" / "archive").is_dir())
        config = (self.project / "openspec" / "config.yaml").read_text()
        self.assertTrue(config.startswith("schema: avengers-sdd\n"), config)
        self.assertIn("# Project context", config)
        self.assertTrue((self.schema_dir() / "schema.yaml").is_file())
        self.assertTrue((self.schema_dir() / "templates" / "tests.md").is_file())
        self.assertFalse((self.project / ".claude").exists())
        self.assertEqual(json.loads(out)["openspec_dir_real"],
                         os.path.realpath(self.project / "openspec"))

    def test_idempotent(self) -> None:
        self.assertEqual(self.run_cli("init")[0], 0)
        count = len(self.calls())
        code, _, err = self.run_cli("init")
        self.assertEqual(code, 2)
        self.assertIn("no-op", err)
        self.assertEqual(len(self.calls()), count)

    def test_existing_dir_extended_without_overwrite(self) -> None:
        spec = self.project / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# auth\n")
        self.assertEqual(self.run_cli("init")[0], 0)
        self.assertEqual(spec.read_text(), "# auth\n")
        self.assertTrue((self.project / "openspec" / "config.yaml").is_file())

    def test_existing_config_kept_schema_added(self) -> None:
        config = self.project / "openspec" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("schema: spec-driven\ncontext: mine\n")
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(config.read_text(), "schema: spec-driven\ncontext: mine\n")
        self.assertNotIn("init", self.subcommands())
        self.assertTrue((self.schema_dir() / "schema.yaml").is_file())
        self.assertEqual(len(json.loads(out)["actions"]), 1)

    def test_schema_copy_matches_plugin(self) -> None:
        self.assertEqual(self.run_cli("init")[0], 0)
        source = ROOT / "references" / "sdd" / "schemas" / "avengers-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                copy = self.schema_dir() / path.relative_to(source)
                self.assertEqual(copy.read_bytes(), path.read_bytes(), str(path))

    def test_dangling_symlink_refused(self) -> None:
        (self.project / "openspec").symlink_to(self.base / "ws" / "openspec")
        code, _, err = self.run_cli("init")
        self.assertEqual(code, 1)
        self.assertIn("dangling symlink", err)
        self.assertIn("--link openspec", err)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.base / "ws").exists())

    def test_through_symlink_lands_in_workstation(self) -> None:
        target = self.base / "ws" / "openspec"
        target.mkdir(parents=True)
        (self.project / "openspec").symlink_to(target, target_is_directory=True)
        self.record_ws(self.base / "ws")
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertTrue((target / "config.yaml").is_file())
        self.assertTrue((self.schema_dir(target) / "schema.yaml").is_file())
        self.assertEqual(json.loads(out)["openspec_dir_real"], os.path.realpath(target))
        # OpenSpec refuses init/archive through a symlink out of the project, so it runs
        # from the workstation, where openspec/ is a real directory.
        self.assertEqual(os.path.realpath(self.calls()[0]["cwd"]), os.path.realpath(target.parent))

    def test_dry_run_changes_nothing(self) -> None:
        code, out, _ = self.run_cli("init", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)["actions"]), 3)
        self.assertFalse((self.project / "openspec").exists())
        self.assertEqual(self.calls(), [])

    def test_init_failure_is_error(self) -> None:
        self.scenario({"init_writes": False, "init": {"exit": 1, "stderr": "boom"}})
        code, _, err = self.run_cli("init")
        self.assertEqual(code, 1)
        self.assertIn("boom", err)
        self.assertFalse(self.schema_dir().exists())


class NewTests(FakeCase):
    def test_pins_schema(self) -> None:
        change_dir = self.project / "openspec" / "changes" / "add-x"
        self.scenario({"new": {"stdout": js({"change": {"id": "add-x", "path": str(change_dir),
                                                        "schema": "avengers-sdd"}})}})
        code, out, err = self.run_cli("new", "add-x", "--schema", "avengers-sdd")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls()[0]["argv"],
                         ["new", "change", "add-x", "--schema", "avengers-sdd", "--json"])
        report = json.loads(out)
        self.assertEqual((report["change"], report["schema"]), ("add-x", "avengers-sdd"))

    def test_invalid_name_refused(self) -> None:
        for name in ("Bad_Name", "x-", "a--b", "a b"):
            with self.subTest(name=name):
                code, _, err = self.run_cli("new", name, "--schema", "spec-driven")
                self.assertEqual(code, 1)
                self.assertIn("kebab-case", err)
        self.assertEqual(self.calls(), [])

    def test_schema_required(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sdd.main(["new", "add-x"])

    def test_unknown_schema_rejected(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
            sdd.main(["new", "add-x", "--schema", "../evil"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("invalid choice", err.getvalue())
        self.assertEqual(self.calls(), [])

    def test_openspec_error_reported(self) -> None:
        self.scenario({"new": {"exit": 1, "stdout": js({"change": None, "status": [
            {"severity": "error", "code": "change_error",
             "message": "Change 'add-x' already exists"}]})}})
        code, _, err = self.run_cli("new", "add-x", "--schema", "spec-driven")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)


class SymlinkCwdTests(FakeCase):
    def test_commands_run_from_workstation(self) -> None:
        target = self.base / "ws" / "openspec"
        target.mkdir(parents=True)
        (self.project / "openspec").symlink_to(target, target_is_directory=True)
        self.record_ws(self.base / "ws")
        self.scenario({"validate": {"stdout": validate_json()}})
        self.assertEqual(self.run_cli("validate", "add-x")[0], 0)
        self.assertEqual(os.path.realpath(self.calls()[0]["cwd"]),
                         os.path.realpath(self.base / "ws"))

    def test_dangling_link_refused_before_openspec_runs(self) -> None:
        (self.project / "openspec").symlink_to(self.base / "gone" / "openspec")
        code, _, err = self.run_cli("validate", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("dangling symlink", err)
        self.assertEqual(self.calls(), [])

    def link_outside(self) -> None:
        target = self.base / "other" / "openspec"
        target.mkdir(parents=True)
        (self.project / "openspec").symlink_to(target, target_is_directory=True)

    def test_link_outside_recorded_workstation_refused(self) -> None:
        self.link_outside()
        (self.base / "ws").mkdir()
        self.record_ws(self.base / "ws")
        for argv in (("validate", "add-x"), ("init",)):
            with self.subTest(argv=argv):
                code, _, err = self.run_cli(*argv)
                self.assertEqual(code, 1)
                self.assertIn("not inside the recorded md workstation", err)
                self.assertIn("--link openspec", err)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.base / "other" / "openspec" / "config.yaml").exists())

    def test_link_without_recorded_workstation_refused(self) -> None:
        self.link_outside()
        code, _, err = self.run_cli("status", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("not inside a recorded md workstation", err)
        self.assertEqual(self.calls(), [])

    def test_malformed_settings_backed_up_and_refused(self) -> None:
        self.link_outside()
        settings = self.project / ".avengers" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text("{bad")
        code, _, err = self.run_cli("validate", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("WARNING: malformed JSON", err)
        self.assertEqual((settings.parent / "settings.json.bak").read_text(), "{bad")

    def test_link_target_not_named_openspec_refused(self) -> None:
        target = self.base / "elsewhere"
        target.mkdir()
        (self.project / "openspec").symlink_to(target, target_is_directory=True)
        code, _, err = self.run_cli("status", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("not named 'openspec'", err)


class ValidateTests(FakeCase):
    def run_validate(self, **kwargs) -> tuple[int, dict, str]:
        self.scenario({"validate": {"stdout": validate_json(**kwargs)}})
        code, out, err = self.run_cli("validate", "add-x")
        return code, json.loads(out), err

    def test_clean(self) -> None:
        code, report, err = self.run_validate()
        self.assertEqual(code, 0, err)
        self.assertTrue(report["valid"])
        self.assertEqual(self.calls()[0]["argv"], ["validate", "add-x", "--type", "change",
                                                   "--strict", "--json", "--no-interactive"])

    def test_archive_would_refuse_info_fails(self) -> None:
        code, report, err = self.run_validate(issues=[{
            "level": "INFO", "path": "greeting/spec.md",
            "message": "Archive would refuse this delta: greeting MODIFIED failed for header "
                       "\"### Requirement: Ghost\" - not found"}])
        self.assertEqual(code, 1)
        self.assertTrue(report["openspec_valid"])
        self.assertFalse(report["valid"])
        self.assertEqual(len(report["blocking"]), 1)
        self.assertIn("archive would refuse", err)

    def test_could_not_check_merge_conflicts_info_fails(self) -> None:
        code, report, _ = self.run_validate(issues=[{
            "level": "INFO", "path": "specs",
            "message": "Could not check archive merge conflicts: ENOENT"}])
        self.assertEqual(code, 1)
        self.assertFalse(report["valid"])

    def test_other_info_passes(self) -> None:
        code, report, err = self.run_validate(issues=[{
            "level": "INFO", "path": "file", "message": "skip_specs accepted"}])
        self.assertEqual(code, 0, err)
        self.assertEqual(report["blocking"], [])

    def test_error_fails(self) -> None:
        code, report, _ = self.run_validate(valid=False, issues=[{
            "level": "ERROR", "path": "file", "message": "Change must have at least one delta"}])
        self.assertEqual(code, 1)
        self.assertFalse(report["valid"])

    def test_unknown_change(self) -> None:
        self.scenario({"validate": {"exit": 1, "stdout": js({"status": [
            {"severity": "error", "code": "unknown_item", "message": "Unknown item 'add-x'"}]})}})
        code, _, err = self.run_cli("validate", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("unknown_item", err)


class StatusTests(FakeCase):
    def status_json(self, statuses: list[tuple[str, str]], root: Path) -> str:
        return js({"changeName": "add-x", "schemaName": "avengers-sdd",
                   "changeRoot": str(root), "isPlanningComplete": all(
                       s == "done" for _, s in statuses),
                   "artifacts": [{"id": i, "status": s} for i, s in statuses]})

    def test_next_artifact_and_realpath(self) -> None:
        real = self.base / "ws" / "openspec" / "changes" / "add-x"
        real.mkdir(parents=True)
        alias = self.base / "alias"
        alias.symlink_to(self.base / "ws", target_is_directory=True)
        self.scenario({"status": {"stdout": self.status_json(
            [("proposal", "done"), ("specs", "ready"), ("design", "ready"),
             ("tests", "blocked"), ("tasks", "blocked")],
            alias / "openspec" / "changes" / "add-x")},
            "list": {"stdout": list_json(done=0, total=0)}})
        code, out, err = self.run_cli("status", "add-x")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report["next"], "specs")
        self.assertEqual((report["tasks_done"], report["tasks_total"]), (0, 0))
        self.assertEqual(report["change_dir_real"], os.path.realpath(real))
        self.assertEqual(report["schema"], "avengers-sdd")

    def test_apply_then_archive(self) -> None:
        done = [("proposal", "done"), ("tasks", "done")]
        for tasks, expected in (((1, 3), "apply"), ((3, 3), "archive")):
            with self.subTest(tasks=tasks):
                self.scenario({"status": {"stdout": self.status_json(done, self.project)},
                               "list": {"stdout": list_json(done=tasks[0], total=tasks[1])}})
                self.assertEqual(json.loads(self.run_cli("status", "add-x")[1])["next"],
                                 expected)

    def test_missing_change(self) -> None:
        self.scenario({"status": {"exit": 1, "stdout": js({"status": [
            {"severity": "error", "code": "change_error", "message": "Change 'add-x' not found"}
        ]})}})
        code, _, err = self.run_cli("status", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


class InstructionsTests(FakeCase):
    def test_passthrough(self) -> None:
        payload = {"artifactId": "tests", "instruction": "derive tests", "template": "# Tests"}
        self.scenario({"instructions": {"stdout": js(payload)}})
        code, out, err = self.run_cli("instructions", "tests", "add-x")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), payload)
        self.assertEqual(self.calls()[0]["argv"],
                         ["instructions", "tests", "--change", "add-x", "--json"])

    def test_invalid_artifact_refused(self) -> None:
        for artifact in ("Tests", "tests;rm", "../x", "1tests", "a b"):
            with self.subTest(artifact=artifact):
                code, _, err = self.run_cli("instructions", artifact, "add-x")
                self.assertEqual(code, 1)
                self.assertIn("invalid artifact id", err)
        self.assertEqual(self.calls(), [])

    def test_error(self) -> None:
        self.scenario({"instructions": {"exit": 1, "stdout": js({"status": [
            {"severity": "error", "code": "change_error", "message": "not found"}]})}})
        self.assertEqual(self.run_cli("instructions", "tests", "add-x")[0], 1)


class ArchiveTests(FakeCase):
    def arrange(self, done: int = 2, total: int = 2, archive: dict | None = None,
                issues: list | None = None) -> None:
        self.scenario({"list": {"stdout": list_json(done=done, total=total)},
                       "validate": {"stdout": validate_json(issues=issues)},
                       "archive": archive if archive is not None else {"stdout": ARCHIVE_OK}})

    def test_success(self) -> None:
        self.arrange()
        code, out, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report["archived_as"], "2026-01-01-add-x")
        self.assertTrue(report["specs_updated"])
        self.assertIsNone(report["allow_incomplete"])
        self.assertEqual(self.subcommands(), ["list", "validate", "archive"])
        self.assertEqual(self.calls()[-1]["argv"], ["archive", "add-x", "-y", "--json"])

    def test_incomplete_tasks_refused(self) -> None:
        self.arrange(done=1, total=3)
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("2 of 3 task(s) incomplete", err)
        self.assertNotIn("archive", self.subcommands())

    def test_zero_tasks_refused(self) -> None:
        self.arrange(done=0, total=0)
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("no tasks", err)
        self.assertNotIn("archive", self.subcommands())

    def test_allow_incomplete_needs_reason(self) -> None:
        self.arrange(done=1, total=3)
        code, _, err = self.run_cli("archive", "add-x", "--allow-incomplete")
        self.assertEqual(code, 1)
        self.assertIn("--reason", err)
        code, out, err = self.run_cli("archive", "add-x", "--allow-incomplete",
                                      "--reason", "task 3 moved to a follow-up change")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["allow_incomplete"],
                         {"reason": "task 3 moved to a follow-up change"})

    def test_validation_refusal_blocks_archive(self) -> None:
        self.arrange(issues=[{"level": "INFO", "path": "a/spec.md",
                              "message": "Archive would refuse this delta: not found"}])
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("failed validation", err)
        self.assertNotIn("archive", self.subcommands())

    def test_empty_stdout_with_exit_zero_is_failure(self) -> None:
        self.arrange(archive={"stdout": "", "exit": 0})
        code, out, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("printed no JSON", err)

    def test_archive_null_is_failure(self) -> None:
        self.arrange(archive={"stdout": js({"archive": None, "root": {}}), "exit": 0})
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("no archive result", err)

    def test_status_error_mapped_to_exit_1(self) -> None:
        self.arrange(archive={"exit": 0, "stdout": js({"archive": None, "status": [{
            "severity": "error", "code": "archive_spec_update_failed",
            "message": "greeting MODIFIED failed for header \"### Requirement: Ghost\"",
            "fix": "Fix the change delta specs and rerun. No files were changed."}]})})
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("archive_spec_update_failed", err)
        self.assertIn("MODIFIED failed", err)
        self.assertIn("No files were changed", err)

    def test_unreadable_task_counts_are_error(self) -> None:
        for done, total in (("two", 2), (1, [3])):
            with self.subTest(done=done, total=total):
                self.scenario({"list": {"stdout": js({"changes": [
                    {"name": "add-x", "completedTasks": done, "totalTasks": total}]})}})
                code, _, err = self.run_cli("archive", "add-x")
                self.assertEqual(code, 1)
                self.assertIn("unreadable task counts", err)
                self.assertNotIn("Traceback", err)
        self.assertNotIn("archive", self.subcommands())

    def test_unknown_change(self) -> None:
        self.arrange()
        self.scenario({"list": {"stdout": list_json(name="other")}})
        code, _, err = self.run_cli("archive", "add-x")
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


class TelemetryTests(FakeCase):
    def test_every_call_disables_telemetry(self) -> None:
        self.scenario({"--version": {"stdout": "1.13.2\n"},
                       "list": {"stdout": list_json()},
                       "validate": {"stdout": validate_json()},
                       "archive": {"stdout": ARCHIVE_OK}})
        self.run_cli("preflight")
        self.run_cli("init")
        self.run_cli("validate", "add-x")
        self.run_cli("archive", "add-x")
        calls = self.calls()
        self.assertGreaterEqual(len(calls), 6)
        for call in calls:
            with self.subTest(argv=call["argv"]):
                self.assertEqual(call["env"], {"OPENSPEC_TELEMETRY": "0", "DO_NOT_TRACK": "1"})
        self.assertEqual(os.environ["OPENSPEC_TELEMETRY"], "1")  # parent env untouched


class CliHelpTests(unittest.TestCase):
    def test_help_for_each_subcommand(self) -> None:
        for argv in ([], ["preflight"], ["init"], ["new"], ["validate"], ["status"],
                     ["instructions"], ["archive"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, str(SCRIPT), *argv, "--help"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage", proc.stdout)


# --------------------------------------------------------------------------- integration

PROPOSAL = """# Proposal

## Why

Users of the service want a friendly greeting that uses their own name.

## What Changes

- Add a named greeting.

## Capabilities

### New Capabilities
- `greeting`: greets a user by name

## Impact

None.
"""
SPEC = """# Spec Delta

## Purpose

Lets users receive a friendly greeting from the service on request.

## ADDED Requirements

### Requirement: Greets by name
The system SHALL greet the user by name.

#### Scenario: Named greeting
- **WHEN** the user asks for a greeting as "Ann"
- **THEN** the system replies "Hello, Ann"
"""
GHOST_SPEC = """## MODIFIED Requirements

### Requirement: Does not exist
The system SHALL do a thing that never existed.

#### Scenario: Ghost
- **WHEN** a ghost appears
- **THEN** nothing happens
"""
TESTS_MD = """# Tests

## greeting

- [x] tests/test_greet.py::test_named_greeting
  - Scenario: Greets by name / Named greeting

## Run

python3 -m unittest tests.test_greet
"""


@unittest.skipUnless(os.environ.get("OPENSPEC_BIN"),
                     "set OPENSPEC_BIN to a real openspec binary to run the integration test")
class IntegrationTests(unittest.TestCase):
    """End to end with the real CLI: avengers-sdd schema through a symlinked openspec/."""

    def setUp(self) -> None:
        binary = Path(os.environ["OPENSPEC_BIN"]).expanduser()
        if not binary.is_file():
            self.fail(f"OPENSPEC_BIN={binary} is not a file")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        home = self.base / "home"
        (home / ".config").mkdir(parents=True)
        env_patch = mock.patch.dict(os.environ, {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_DATA_HOME": str(home / ".local" / "share"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "PATH": str(binary.parent) + os.pathsep + os.environ.get("PATH", ""),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.base),
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.binary = binary
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.ws = self.base / "md" / "repo-mds"
        subprocess.run(["git", *GIT_IDENTITY, "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", *GIT_IDENTITY, "commit", "--allow-empty", "-q", "-m", "init"],
                       cwd=self.repo, check=True)

    def cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sdd.main([*args, "--project-dir", str(self.repo)])
        return code, out.getvalue(), err.getvalue()

    def openspec(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.binary), *args], cwd=self.repo, capture_output=True,
                              text=True, check=False, env=sdd.openspec_env())

    def write_change(self, change: str, spec: str, tasks: str) -> Path:
        path = self.repo / "openspec" / "changes" / change
        (path / "specs" / "greeting").mkdir(parents=True, exist_ok=True)
        (path / "proposal.md").write_text(PROPOSAL)
        (path / "specs" / "greeting" / "spec.md").write_text(spec)
        (path / "design.md").write_text("# Design\n\n## Context\n\nA single function.\n")
        (path / "tests.md").write_text(TESTS_MD)
        (path / "tasks.md").write_text(tasks)
        return path

    def test_end_to_end_through_symlinked_openspec(self) -> None:
        code, out, err = self.cli("preflight")
        self.assertEqual(code, 0, err)
        version = json.loads(out)["openspec"]["version"]
        if version != sdd.PINNED_OPENSPEC:
            print(f"\nWARNING: OpenSpec {version} differs from the pinned "
                  f"{sdd.PINNED_OPENSPEC}", file=sys.stderr)

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ws_code = workstation.main(["set", "--path", str(self.ws), "--link", "openspec",
                                        "--project-dir", str(self.repo)])
        self.assertEqual(ws_code, 0)
        self.assertTrue((self.repo / "openspec").is_symlink())

        code, out, err = self.cli("init")
        self.assertEqual(code, 0, err)
        real = self.ws / "openspec"
        self.assertTrue((real / "config.yaml").is_file())
        self.assertTrue((real / "config.yaml").read_text().startswith("schema: avengers-sdd"))
        self.assertTrue((real / "schemas" / "avengers-sdd" / "schema.yaml").is_file())
        self.assertFalse((self.repo / ".claude" / "commands").exists())
        self.assertEqual(self.cli("init")[0], 2)

        # Hulk W5: the project schema resolves through the symlink.
        which = self.openspec("schema", "which", "avengers-sdd", "--json")
        self.assertEqual(which.returncode, 0, which.stderr)
        resolved = json.loads(which.stdout)
        self.assertEqual(resolved["source"], "project")
        self.assertEqual(os.path.realpath(resolved["path"]),
                         os.path.realpath(real / "schemas" / "avengers-sdd"))
        schema_check = self.openspec("schema", "validate", "avengers-sdd", "--json")
        self.assertEqual(schema_check.returncode, 0, schema_check.stdout + schema_check.stderr)

        code, out, err = self.cli("new", "add-greeting", "--schema", "avengers-sdd")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["change_dir_real"],
                         os.path.realpath(real / "changes" / "add-greeting"))
        self.assertIn("schema: avengers-sdd",
                      (real / "changes" / "add-greeting" / ".openspec.yaml").read_text())

        code, out, err = self.cli("status", "add-greeting")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual([a["id"] for a in report["artifacts"]],
                         ["proposal", "specs", "design", "tests", "tasks"])
        self.assertEqual(report["next"], "proposal")
        code, out, err = self.cli("instructions", "tests", "add-greeting")
        self.assertEqual(code, 0, err)
        self.assertIn("one failing test per WHEN/THEN scenario",
                      " ".join(json.loads(out)["instruction"].split()))

        tasks = "# Tasks\n\n## 1. Greeting\n\n- [x] 1.1 Write the failing test\n- [ ] 1.2 Greet\n"
        self.write_change("add-greeting", SPEC, tasks)
        code, out, err = self.cli("status", "add-greeting")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual((report["tasks_done"], report["tasks_total"], report["next"]),
                         (1, 2, "apply"))
        self.assertEqual(self.cli("validate", "add-greeting")[0], 0)

        code, _, err = self.cli("archive", "add-greeting")
        self.assertEqual(code, 1)
        self.assertIn("incomplete", err)
        self.assertTrue((real / "changes" / "add-greeting").is_dir())

        self.write_change("add-greeting", SPEC, tasks.replace("- [ ]", "- [x]"))
        code, out, err = self.cli("archive", "add-greeting")
        self.assertEqual(code, 0, err)
        self.assertTrue(json.loads(out)["specs_updated"])
        self.assertIn("Greets by name", (real / "specs" / "greeting" / "spec.md").read_text())
        self.assertFalse((real / "changes" / "add-greeting").exists())

        # A MODIFIED delta for a requirement that does not exist: OpenSpec's strict
        # validate passes it (INFO only); the wrapper refuses it.
        self.assertEqual(self.cli("new", "ghost", "--schema", "spec-driven")[0], 0)
        # Quick track: spec-driven's tasks require design, so next stays on design
        # until design.md exists; a one-line "Not needed" design unblocks tasks.
        ghost = real / "changes" / "ghost"
        (ghost / "specs" / "greeting").mkdir(parents=True)
        (ghost / "proposal.md").write_text(PROPOSAL)
        (ghost / "specs" / "greeting" / "spec.md").write_text(GHOST_SPEC)
        self.assertEqual(json.loads(self.cli("status", "ghost")[1])["next"], "design")
        (ghost / "design.md").write_text("# Design\n\nNot needed: a one-line change.\n")
        self.assertEqual(json.loads(self.cli("status", "ghost")[1])["next"], "tasks")
        self.write_change("ghost", GHOST_SPEC, "# Tasks\n\n## 1. G\n\n- [x] 1.1 Do it\n")
        raw = self.openspec("validate", "ghost", "--type", "change", "--strict", "--json")
        self.assertEqual(raw.returncode, 0, raw.stdout)
        code, out, _ = self.cli("validate", "ghost")
        self.assertEqual(code, 1)
        self.assertTrue(json.loads(out)["openspec_valid"])
        code, _, err = self.cli("archive", "ghost")
        self.assertEqual(code, 1)
        self.assertTrue((real / "changes" / "ghost").is_dir())


if __name__ == "__main__":
    unittest.main()
