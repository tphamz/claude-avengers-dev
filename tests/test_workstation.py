"""Tests for skills/avengers-workstation/scripts/workstation.py (stdlib unittest).

HOME is patched to a temp dir for every test, so ~/.avengers is never touched.

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

SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "avengers-workstation" / "scripts"
          / "workstation.py")
_spec = importlib.util.spec_from_file_location("workstation", SCRIPT)
workstation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(workstation)

GIT_IDENTITY = ["-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"]


class WSCase(unittest.TestCase):
    """A temp HOME, a code repo, and an md root, all under one temp dir."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.home = self.base / "home"
        self.home.mkdir()
        env_patch = mock.patch.dict(os.environ, {
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self.base),
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.md = self.base / "md"
        self.git("init", "-q")
        self.commit("chore: init", {"README.md": "r\n"})

    # -- helpers ---------------------------------------------------------------

    def git(self, *args: str, cwd: Path | None = None) -> str:
        proc = subprocess.run(["git", *GIT_IDENTITY, *args], cwd=cwd or self.repo,
                              capture_output=True, text=True, check=True)
        return proc.stdout.strip()

    def write(self, rel: str, content: str = "x\n", base: Path | None = None) -> Path:
        path = (base or self.repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def commit(self, message: str, files: dict[str, str] | None = None) -> str:
        for rel, content in (files or {}).items():
            self.write(rel, content)
        self.git("add", "-A")
        self.git("commit", "--allow-empty", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def run_cli(self, *args: str, project: Path | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = workstation.main([*args, "--project-dir", str(project or self.repo)])
        return code, out.getvalue(), err.getvalue()

    def resolve(self, project: Path | None = None) -> dict:
        code, out, err = self.run_cli("resolve", project=project)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def registry(self) -> dict:
        path = self.home / ".avengers" / "workstations.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def write_registry(self, data: dict) -> None:
        self.write(".avengers/workstations.json", json.dumps(data), base=self.home)

    def settings(self) -> dict:
        path = self.repo / ".avengers" / "settings.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def exclude_lines(self) -> list[str]:
        path = Path(self.git("rev-parse", "--path-format=absolute", "--git-path",
                             "info/exclude"))
        return path.read_text().splitlines() if path.exists() else []

    def set_ws(self, path: Path | None = None) -> tuple[int, str, str]:
        return self.run_cli("set", "--path", str(path or self.md / "repo"))


class NormalizeRemoteTests(unittest.TestCase):
    def test_ssh_and_https_normalize_equal(self) -> None:
        expected = "github.com/Org/Repo"
        for url in ("git@github.com:Org/Repo.git",
                    "https://github.com/Org/Repo.git",
                    "https://user@GitHub.com:443/Org/Repo.git",
                    "ssh://git@github.com:22/Org/Repo.git",
                    "https://github.com/Org/Repo/"):
            with self.subTest(url=url):
                self.assertEqual(workstation.normalize_remote(url), expected)

    def test_gitlab_subgroups_kept(self) -> None:
        self.assertEqual(workstation.normalize_remote("git@gitlab.com:grp/sub/proj.git"),
                         "gitlab.com/grp/sub/proj")

    def test_local_path(self) -> None:
        self.assertEqual(workstation.normalize_remote("/srv/git/proj.git/"), "/srv/git/proj.git")


class ResolveTests(WSCase):
    def test_missing(self) -> None:
        report = self.resolve()
        self.assertEqual(report["state"], "missing")
        self.assertIsNone(report["path"])
        self.assertEqual(report["symlink"], "missing")
        self.assertEqual(report["repo_name"], "repo")

    def test_project_setting(self) -> None:
        (self.md / "repo").mkdir(parents=True)
        self.write(".avengers/settings.json", json.dumps({"mdWorkstation": str(self.md / "repo")}))
        report = self.resolve()
        self.assertEqual((report["state"], report["source"]), ("ok", "project"))

    def test_registry_by_ssh_matches_https_registration(self) -> None:
        self.git("remote", "add", "origin", "git@github.com:Org/Repo.git")
        (self.md / "Repo").mkdir(parents=True)
        self.write_registry({"root": str(self.md),
                             "repos": {workstation.normalize_remote(
                                 "https://github.com/Org/Repo.git"): str(self.md / "Repo")}})
        report = self.resolve()
        self.assertEqual((report["state"], report["source"]), ("ok", "registry"))
        self.assertEqual(report["remote_key"], "github.com/Org/Repo")
        self.assertEqual(report["repo_name"], "Repo")

    def test_upstream_only_remote(self) -> None:
        self.git("remote", "add", "upstream", "https://example.com/team/svc.git")
        self.git("remote", "add", "aaa", "https://example.com/fork/svc.git")
        self.assertEqual(self.resolve()["remote_key"], "example.com/team/svc")

    def test_first_remote_alphabetically(self) -> None:
        self.git("remote", "add", "zed", "https://example.com/z/svc.git")
        self.git("remote", "add", "bee", "https://example.com/b/svc.git")
        self.assertEqual(self.resolve()["remote_key"], "example.com/b/svc")

    def test_no_remote_worktrees_share_key(self) -> None:
        other = self.base / "wt2"
        self.git("worktree", "add", "-q", str(other), "-b", "other")
        key_main = self.resolve()["remote_key"]
        key_wt = self.resolve(project=other)["remote_key"]
        self.assertEqual(key_main, key_wt)
        self.assertEqual(key_main, os.path.realpath(self.repo / ".git"))

    def test_second_worktree_finds_workstation_without_asking(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        other = self.base / "wt2"
        self.git("worktree", "add", "-q", str(other), "-b", "other")
        report = self.resolve(project=other)
        self.assertEqual((report["state"], report["source"]), ("ok", "registry"))
        self.assertEqual(report["symlink"], "missing")
        code, _, err = self.run_cli("set", "--path", report["path"], project=other)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.resolve(project=other)["symlink"], "ok")

    def test_guess(self) -> None:
        (self.md / "repo").mkdir(parents=True)
        self.write_registry({"root": str(self.md), "repos": {}})
        report = self.resolve()
        self.assertEqual((report["state"], report["source"]), ("guess", "guess"))
        self.assertEqual(report["path"], str(self.md / "repo"))

    def test_broken_recorded_path(self) -> None:
        self.write(".avengers/settings.json", json.dumps({"mdWorkstation": str(self.md / "gone")}))
        self.assertEqual(self.resolve()["state"], "broken")

    def test_dangling_symlink_is_broken(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        (self.md / "repo" / "avengers").rmdir()
        (self.md / "repo").rmdir()
        report = self.resolve()
        self.assertEqual((report["state"], report["symlink"]), ("broken", "dangling"))

    def test_in_repo_choice(self) -> None:
        code, _, _ = self.run_cli("set", "--in-repo")
        self.assertEqual(code, 0)
        self.assertEqual(self.resolve()["state"], "in_repo")
        self.assertEqual(self.run_cli("set", "--in-repo")[0], 2)

    def test_malformed_registry_backed_up(self) -> None:
        self.write(".avengers/workstations.json", "{bad", base=self.home)
        code, _, err = self.run_cli("resolve")
        self.assertEqual(code, 0)
        self.assertIn("WARNING", err)
        self.assertTrue((self.home / ".avengers" / "workstations.json.bak").exists())


class SetTests(WSCase):
    def test_symlink_settings_registry_and_exclude(self) -> None:
        code, out, err = self.set_ws()
        self.assertEqual(code, 0, err)
        ws = self.md / "repo"
        link = self.repo / "_bmad-output"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.path.realpath(link), os.path.realpath(ws))
        self.assertTrue((ws / "avengers").is_dir())
        self.assertEqual(self.settings()["mdWorkstation"], str(ws))
        self.assertEqual(self.registry()["root"], str(self.md))
        self.assertIn(str(ws), self.registry()["repos"].values())
        lines = self.exclude_lines()
        self.assertIn("/_bmad-output", lines)
        self.assertNotIn("/_bmad-output/", lines)
        self.assertIn("/.claude/rules/avengers-kb.md", lines)
        self.assertNotIn("_bmad-output", self.git("status", "--porcelain"))
        self.assertEqual(json.loads(out)["path"], str(ws))

    def test_idempotent(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        code, _, err = self.set_ws()
        self.assertEqual(code, 2)
        self.assertIn("no-op", err)

    def test_repairs_dangling_symlink(self) -> None:
        (self.repo / "_bmad-output").symlink_to(self.base / "nowhere")
        self.assertEqual(self.set_ws()[0], 0)
        self.assertEqual(self.resolve()["symlink"], "ok")

    def test_replaces_empty_real_dir(self) -> None:
        (self.repo / "_bmad-output").mkdir()
        self.assertEqual(self.set_ws()[0], 0)
        self.assertTrue((self.repo / "_bmad-output").is_symlink())

    def test_refuses_non_empty_real_dir(self) -> None:
        self.write("_bmad-output/prd.md", "# prd\n")
        code, _, err = self.set_ws()
        self.assertEqual(code, 1)
        self.assertIn("migrate", err)
        self.assertFalse((self.repo / "_bmad-output").is_symlink())

    def test_refuses_tracked_even_if_empty(self) -> None:
        self.commit("docs: prd", {"_bmad-output/prd.md": "# prd\n"})
        (self.repo / "_bmad-output" / "prd.md").unlink()
        (self.repo / "_bmad-output").rmdir()
        self.assertTrue(self.git("ls-files", "--", "_bmad-output"))
        code, _, err = self.set_ws()
        self.assertEqual(code, 1)
        self.assertIn("tracked", err)
        self.assertFalse((self.repo / "_bmad-output").exists())

    def test_collision_suggests_org_prefix(self) -> None:
        self.git("remote", "add", "origin", "git@github.com:acme/repo.git")
        self.write_registry({"root": str(self.md),
                             "repos": {"github.com/other/repo": str(self.md / "repo")}})
        code, _, err = self.set_ws()
        self.assertEqual(code, 1)
        self.assertIn(str(self.md / "acme-repo"), err)

    def test_refuses_workstation_inside_repo(self) -> None:
        code, _, err = self.set_ws(self.repo / "docs-ws")
        self.assertEqual(code, 1)
        self.assertIn("inside the project", err)

    def test_dry_run_changes_nothing(self) -> None:
        code, out, _ = self.run_cli("set", "--path", str(self.md / "repo"), "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["actions"])
        self.assertFalse((self.repo / "_bmad-output").exists())
        self.assertFalse((self.md / "repo").exists())
        self.assertEqual(self.settings(), {})
        self.assertEqual(self.registry(), {})
        self.assertNotIn("/_bmad-output", self.exclude_lines())

    def test_explicit_root_recorded(self) -> None:
        code, _, _ = self.run_cli("set", "--path", str(self.md / "repo"),
                                  "--root", str(self.base / "mdroot"))
        self.assertEqual(code, 0)
        self.assertEqual(self.registry()["root"], str(self.base / "mdroot"))

    def test_story_automator_warning(self) -> None:
        (self.home / ".claude" / "skills" / "bmad-story-automator").mkdir(parents=True)
        code, _, err = self.set_ws()
        self.assertEqual(code, 0)
        self.assertIn("bmad-story-automator", err)

    def test_custom_output_folder(self) -> None:
        self.write("_bmad/bmm/config.yaml", 'output_folder: "{project-root}/out/md"\n')
        self.assertEqual(self.set_ws()[0], 0)
        self.assertTrue((self.repo / "out" / "md").is_symlink())
        self.assertIn("/out/md", self.exclude_lines())


class MigrateTests(WSCase):
    def test_untracked_content_moves(self) -> None:
        self.write("_bmad-output/planning-artifacts/prd.md", "# prd\n")
        code, out, err = self.run_cli("migrate", "--path", str(self.md / "repo"))
        self.assertEqual(code, 0, err)
        self.assertTrue((self.repo / "_bmad-output").is_symlink())
        self.assertEqual((self.md / "repo" / "planning-artifacts" / "prd.md").read_text(),
                         "# prd\n")
        self.assertEqual((self.repo / "_bmad-output" / "planning-artifacts" / "prd.md")
                         .read_text(), "# prd\n")
        self.assertIsNotNone(json.loads(out)["set"])

    def test_tracked_without_untrack_refuses(self) -> None:
        self.commit("docs: prd", {"_bmad-output/prd.md": "# prd\n"})
        code, _, err = self.run_cli("migrate", "--path", str(self.md / "repo"))
        self.assertEqual(code, 1)
        self.assertIn("LOSES", err)
        self.assertTrue((self.repo / "_bmad-output" / "prd.md").is_file())
        self.assertFalse((self.md / "repo").exists())

    def test_tracked_with_untrack_leaves_removal_uncommitted(self) -> None:
        self.commit("docs: prd", {"_bmad-output/prd.md": "# prd\n"})
        head = self.git("rev-parse", "HEAD")
        code, _, err = self.run_cli("migrate", "--path", str(self.md / "repo"), "--untrack")
        self.assertEqual(code, 0, err)
        self.assertIn("LOSES", err)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertIn("D  _bmad-output/prd.md", self.git("status", "--porcelain"))
        self.assertTrue((self.md / "repo" / "prd.md").is_file())

    def test_conflict_suffix_and_identical_dropped(self) -> None:
        ws = self.md / "repo"
        self.write("prd.md", "workstation copy\n", base=ws)
        self.write("same.md", "same\n", base=ws)
        self.write("_bmad-output/prd.md", "repo copy\n")
        self.write("_bmad-output/same.md", "same\n")
        code, out, err = self.run_cli("migrate", "--path", str(ws))
        self.assertEqual(code, 0, err)
        self.assertEqual((ws / "prd.md").read_text(), "workstation copy\n")
        self.assertEqual((ws / "prd.conflict.md").read_text(), "repo copy\n")
        self.assertFalse((ws / "same.conflict.md").exists())
        self.assertEqual(json.loads(out)["conflicts"], [str(ws / "prd.conflict.md")])

    def test_dry_run_moves_nothing(self) -> None:
        self.write("_bmad-output/prd.md", "# prd\n")
        code, out, _ = self.run_cli("migrate", "--path", str(self.md / "repo"), "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)["moves"]), 1)
        self.assertTrue((self.repo / "_bmad-output" / "prd.md").is_file())
        self.assertFalse((self.md / "repo").exists())

    def test_nothing_to_migrate(self) -> None:
        code, _, _ = self.run_cli("migrate", "--path", str(self.md / "repo"))
        self.assertEqual(code, 2)


BMM = """# BMM Module Configuration
planning_artifacts: "{project-root}/_bmad-output/planning-artifacts"
project_knowledge: '{project-root}/docs'  # the KB lives here
story_notes: "{output_folder}/notes"
user_name: Tan
output_folder: "{project-root}/_bmad-output"
"""
TEA = """test_artifacts: "{project-root}/qa/artifacts"
test_design_output: _bmad-output/test-artifacts/test-design
output_folder: "{project-root}/_bmad-output"
"""


class ConfigTests(WSCase):
    def setUp(self) -> None:
        super().setUp()
        self.bmm = self.write("_bmad/bmm/config.yaml", BMM)
        self.tea = self.write("_bmad/tea/config.yaml", TEA)

    def check(self) -> tuple[int, dict]:
        code, out, _ = self.run_cli("check-config")
        return code, json.loads(out)

    def test_lists_outside_keys_with_placeholders_expanded(self) -> None:
        code, report = self.check()
        self.assertEqual(code, 2)
        keys = {(e["module"], e["key"]) for e in report["outside"]}
        self.assertEqual(keys, {("bmm", "project_knowledge"), ("tea", "test_artifacts")})
        pk = next(e for e in report["outside"] if e["key"] == "project_knowledge")
        self.assertEqual(pk["resolved"], str(self.repo / "docs"))
        self.assertEqual(pk["suggested"], "{project-root}/_bmad-output/project-knowledge")
        self.assertFalse(pk["declined"])

    def test_all_inside_exits_zero(self) -> None:
        self.bmm.write_text('output_folder: _bmad-output\nproject_knowledge: '
                            '"{output_folder}/kb"\n')
        self.tea.unlink()
        self.assertEqual(self.check()[0], 0)

    def test_repoint_keeps_comment_and_backs_up(self) -> None:
        code, out, err = self.run_cli("repoint-config", "--key", "project_knowledge")
        self.assertEqual(code, 0, err)
        text = self.bmm.read_text()
        self.assertIn('project_knowledge: "{project-root}/_bmad-output/project-knowledge"'
                      '  # the KB lives here\n', text)
        self.assertIn("# BMM Module Configuration\n", text)
        self.assertIn("user_name: Tan\n", text)
        self.assertEqual((self.repo / "_bmad" / "bmm" / "config.yaml.bak").read_text(), BMM)
        self.assertNotIn("project_knowledge", {e["key"] for e in self.check()[1]["outside"]})
        self.assertEqual(self.run_cli("repoint-config", "--key", "project_knowledge")[0], 2)

    def test_repoint_tea_key(self) -> None:
        self.assertEqual(self.run_cli("repoint-config", "--key", "test_artifacts")[0], 0)
        self.assertIn('test_artifacts: "{project-root}/_bmad-output/test-artifacts"',
                      self.tea.read_text())

    def test_repoint_dry_run(self) -> None:
        code, out, _ = self.run_cli("repoint-config", "--key", "project_knowledge", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)["changes"]), 1)
        self.assertEqual(self.bmm.read_text(), BMM)
        self.assertFalse((self.repo / "_bmad" / "bmm" / "config.yaml.bak").exists())

    def test_unknown_key_is_error(self) -> None:
        self.assertEqual(self.run_cli("repoint-config", "--key", "nope")[0], 1)

    def test_decline_is_recorded(self) -> None:
        self.assertEqual(self.run_cli("repoint-config", "--key", "project_knowledge",
                                      "--decline")[0], 0)
        self.assertEqual(self.settings()["mdRepointDeclined"], ["project_knowledge"])
        pk = next(e for e in self.check()[1]["outside"] if e["key"] == "project_knowledge")
        self.assertTrue(pk["declined"])
        self.assertEqual(self.run_cli("repoint-config", "--key", "project_knowledge",
                                      "--decline")[0], 2)
        self.assertEqual(self.bmm.read_text(), BMM)


class MdStatusTests(WSCase):
    def setUp(self) -> None:
        super().setUp()
        self.mdrepo = self.base / "mdrepo"
        self.mdrepo.mkdir()
        self.git("init", "-q", cwd=self.mdrepo)
        self.write("other/notes.md", "n\n", base=self.mdrepo)
        self.git("add", "-A", cwd=self.mdrepo)
        self.git("commit", "-q", "-m", "init", cwd=self.mdrepo)
        self.ws = self.mdrepo / "team" / "repo"

    def test_scoped_to_workstation_subdir(self) -> None:
        self.assertEqual(self.set_ws(self.ws)[0], 0)
        self.write("planning-artifacts/prd.md", "# prd\n", base=self.ws)
        self.write("other/notes.md", "changed\n", base=self.mdrepo)
        code, out, err = self.run_cli("md-status")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertEqual(report["rel"], "team/repo")
        self.assertEqual(report["toplevel"], os.path.realpath(self.mdrepo))
        self.assertEqual(report["dirty"], ["team/repo/planning-artifacts/prd.md"])
        self.assertEqual(report["repo_name"], "repo")

    def test_clean_is_noop(self) -> None:
        self.assertEqual(self.set_ws(self.ws)[0], 0)
        self.write("prd.md", "# prd\n", base=self.ws)
        self.git("add", "-A", cwd=self.mdrepo)
        self.git("commit", "-q", "-m", "ws", cwd=self.mdrepo)
        self.write("other/notes.md", "changed outside the workstation\n", base=self.mdrepo)
        self.assertEqual(self.run_cli("md-status")[0], 2)

    def test_not_a_git_repo(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        code, out, _ = self.run_cli("md-status")
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(out)["git"])


class UnlinkTests(WSCase):
    def test_keeps_contents(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        self.write("_bmad-output/prd.md", "# prd\n")
        code, out, err = self.run_cli("unlink")
        self.assertEqual(code, 0, err)
        self.assertFalse((self.repo / "_bmad-output").exists())
        self.assertEqual((self.md / "repo" / "prd.md").read_text(), "# prd\n")
        self.assertNotIn("mdWorkstation", self.settings())
        self.assertNotIn("/_bmad-output", self.exclude_lines())
        self.assertNotIn("/.claude/rules/avengers-kb.md", self.exclude_lines())
        self.assertTrue(self.registry()["repos"])
        self.assertEqual(json.loads(out)["kept"], str(self.md / "repo"))
        self.assertEqual(self.run_cli("unlink")[0], 2)

    def test_dry_run(self) -> None:
        self.assertEqual(self.set_ws()[0], 0)
        self.assertEqual(self.run_cli("unlink", "--dry-run")[0], 0)
        self.assertTrue((self.repo / "_bmad-output").is_symlink())


class GrantPathTests(WSCase):
    def test_realpath(self) -> None:
        real = self.base / "real-md"
        real.mkdir()
        alias = self.base / "alias-md"
        alias.symlink_to(real)
        self.assertEqual(self.set_ws(alias / "repo")[0], 0)
        code, out, _ = self.run_cli("grant-path")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), os.path.realpath(real / "repo"))

    def test_unresolved_is_error(self) -> None:
        self.assertEqual(self.run_cli("grant-path")[0], 1)


class CliHelpTests(unittest.TestCase):
    def test_help_for_each_subcommand(self) -> None:
        for argv in ([], ["resolve"], ["set"], ["migrate"], ["check-config"],
                     ["repoint-config"], ["md-status"], ["grant-path"], ["unlink"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([sys.executable, str(SCRIPT), *argv, "--help"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage", proc.stdout)


if __name__ == "__main__":
    unittest.main()
