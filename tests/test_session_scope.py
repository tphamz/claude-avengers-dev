"""Tests for the workspace scope guard (stdlib unittest).

Covers four things:

1. `scripts/lib/avengers-scope.sh::avengers_scope_state` - the shared resolver,
   exercised against roots inside a tmpdir so the suite is machine-independent.
2. Where the roots come from: the `AVENGERS_SCOPE_ROOTS` env list, the
   `avengers-scope` file under CLAUDE_CONFIG_DIR (or ~/.claude), and neither. With
   neither, the persona applies everywhere, exactly as before scoping existed.
3. The two guards, end to end, by running the hook scripts and inspecting stdout.
   The fail directions are deliberately opposite: the banner prints on
   `yes|unknown`, the persona injection prints on `yes` only.
4. The `Avengers plugin root:` line, which must print in EVERY scope - IronMan's
   dispatch protocol reads it for the absolute workstation.py path.

Every subprocess gets HOME and CLAUDE_CONFIG_DIR pointed into a tmpdir, so the
user's real configuration is never read.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "scripts" / "lib" / "avengers-scope.sh"
SESSION_START = ROOT / "scripts" / "session-start.sh"
COMPACT_RESUME = ROOT / "scripts" / "compact-resume.sh"
SCOPE_FILE = "avengers-scope"

# Output markers.
BANNER = "⚡ AVENGERS DEV ⚡"
PERSONA = "Tony Stark / Iron Man"
# Both hooks explain an `unknown` scope in the same words, so one phrase matches
# either; COMPACT_NOTE is the half that only compact-resume.sh prints.
UNKNOWN_NOTE = "scope could not be determined"
COMPACT_NOTE = "rule re-injection was skipped"
PLUGIN_LINE = "Avengers plugin root:"
COMPACT_BODY = "Context Resumed"
# The idle-team check: compaction is when an orchestrator forgot its teams.
COMPACT_DISPATCH = "Check now for idle teams and dispatch their next work"
EXPECTED_PLUGIN_LINE = f"{PLUGIN_LINE} {ROOT}"
# The session's project dir, for `pair-registry.py --project-dir`; in scope only.
PROJECT_LINE = "Avengers project dir:"

# Variables the parent environment must not leak into a scope decision.
SCOPE_VARS = ("CLAUDE_PROJECT_DIR", "AVENGERS_SCOPE_ROOTS", "CLAUDE_CONFIG_DIR", "HOME")


class ScopeFixture(unittest.TestCase):
    """A tmpdir with a workspace, a sub-repo, a prefix sibling and an outsider.

    HOME and CLAUDE_CONFIG_DIR live inside the tmpdir too, and start with no
    scope file, so every test begins unconfigured.
    """

    def setUp(self) -> None:
        # `pwd -P` resolves symlinks and the system temp dir may itself be one,
        # so every expected path is the resolved one.
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.workspace = self.tmp / "workspace"
        self.repo_a = self.workspace / "repo-a"
        self.sibling = self.tmp / "workspace-other"
        self.elsewhere = self.tmp / "elsewhere"
        self.home = self.tmp / "home"
        self.config = self.tmp / "config"
        for path in (self.repo_a, self.sibling, self.elsewhere, self.home, self.config):
            path.mkdir(parents=True)
        self.env_roots: str | None = None
        self.config_dir: str | None = str(self.config)

    # -- configuration helpers -------------------------------------------------

    def write_scope_file(self, text: str, directory: Path | None = None) -> Path:
        path = (directory or self.config) / SCOPE_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def env(self, project_dir: str | None = None) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in SCOPE_VARS}
        env["HOME"] = str(self.home)
        if self.config_dir is not None:
            env["CLAUDE_CONFIG_DIR"] = self.config_dir
        if self.env_roots is not None:
            env["AVENGERS_SCOPE_ROOTS"] = self.env_roots
        if project_dir is not None:
            env["CLAUDE_PROJECT_DIR"] = project_dir
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        return env

    # -- runners ---------------------------------------------------------------

    def resolve(self, *args: str, project_dir: str | None = None,
                cwd: Path | None = None) -> str:
        """Call avengers_scope_state with exactly `args`; return its answer."""
        # In `bash -c SCRIPT NAME ARGS...` the lib path lands in $0, so the caller's
        # arguments are already exactly "$@" - do NOT shift.
        argv = ["bash", "-c", '. "$0"; avengers_scope_state "$@"', str(LIB), *args]
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30,
                              check=True, cwd=str(cwd or self.tmp),
                              env=self.env(project_dir), stdin=subprocess.DEVNULL)
        return proc.stdout.strip()

    def state(self, directory: Path | str) -> str:
        """Scope of one directory under the current configuration."""
        return self.resolve(str(directory))

    def run_hook(self, script: Path, project_dir: Path | str | None,
                 cwd: Path | None = None) -> str:
        """Run a hook script with a controlled environment; return stdout."""
        proc = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True, timeout=30,
            check=True, cwd=str(cwd or self.tmp),
            env=self.env(None if project_dir is None else str(project_dir)),
            stdin=subprocess.DEVNULL)
        return proc.stdout

    def scope_to_workspace(self) -> None:
        self.env_roots = str(self.workspace)


class UnconfiguredTests(ScopeFixture):
    """No env var, no file: unscoped, so behaviour matches the unscoped hooks."""

    def test_every_directory_is_in_scope(self) -> None:
        for directory in (self.workspace, self.repo_a, self.sibling, self.elsewhere):
            with self.subTest(directory=directory.name):
                self.assertEqual(self.state(directory), "yes")

    def test_even_an_unresolvable_directory_is_in_scope(self) -> None:
        """Unscoped means no measurement is needed, so nothing can be `unknown`."""
        self.assertEqual(self.state(self.tmp / "gone"), "yes")
        self.assertEqual(self.state(""), "yes")

    def test_default_config_dir_without_a_file_is_unconfigured(self) -> None:
        self.config_dir = None
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_empty_env_var_is_unset(self) -> None:
        self.env_roots = ""
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_env_var_of_only_separators_is_unset(self) -> None:
        self.env_roots = ":: :"
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_file_of_only_comments_and_blanks_is_unconfigured(self) -> None:
        self.write_scope_file("# no roots yet\n\n   \n  # indented comment\n")
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_session_start_prints_banner_and_persona(self) -> None:
        out = self.run_hook(SESSION_START, self.elsewhere)
        self.assertIn(BANNER, out)
        self.assertIn(PERSONA, out)
        self.assertNotIn(UNKNOWN_NOTE, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_compact_resume_prints_the_reinjection(self) -> None:
        out = self.run_hook(COMPACT_RESUME, self.elsewhere)
        self.assertIn(COMPACT_BODY, out)
        self.assertIn(COMPACT_DISPATCH, out)
        self.assertNotIn(UNKNOWN_NOTE, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)


class ScopeResolverTests(ScopeFixture):
    """Matching rules, with the roots passed in the env list."""

    def setUp(self) -> None:
        super().setUp()
        self.scope_to_workspace()

    def test_root_itself_is_in_scope(self) -> None:
        self.assertEqual(self.state(self.workspace), "yes")

    def test_sub_repo_is_in_scope(self) -> None:
        self.assertEqual(self.state(self.repo_a), "yes")

    def test_deeply_nested_path_is_in_scope(self) -> None:
        deep = self.repo_a / "src" / "lib"
        deep.mkdir(parents=True)
        self.assertEqual(self.state(deep), "yes")

    def test_unrelated_path_is_out_of_scope(self) -> None:
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_sibling_sharing_a_prefix_is_out_of_scope(self) -> None:
        """The classic prefix bug: <root>-other must not match <root>."""
        self.assertEqual(self.state(self.sibling), "no")

    def test_parent_of_root_is_out_of_scope(self) -> None:
        self.assertEqual(self.state(self.tmp), "no")

    def test_empty_dir_is_unknown(self) -> None:
        self.assertEqual(self.state(""), "unknown")

    def test_nonexistent_path_is_unknown(self) -> None:
        """Unresolvable is reported as unknown, never as out-of-scope."""
        self.assertEqual(self.state(self.tmp / "no-such-dir"), "unknown")

    def test_nonexistent_path_under_the_root_is_unknown(self) -> None:
        self.assertEqual(self.state(self.workspace / "not-cloned-yet"), "unknown")

    def test_trailing_slashes_do_not_break_the_match(self) -> None:
        self.env_roots = f"{self.workspace}///"
        self.assertEqual(self.state(f"{self.repo_a}/"), "yes")
        self.assertEqual(self.state(f"{self.repo_a}///"), "yes")
        self.assertEqual(self.state(f"{self.sibling}/"), "no")

    def test_symlink_into_the_root_is_in_scope(self) -> None:
        link = self.tmp / "link-to-repo"
        link.symlink_to(self.repo_a)
        self.assertEqual(self.state(link), "yes")

    def test_symlink_out_of_the_root_is_out_of_scope(self) -> None:
        link = self.repo_a / "link-to-elsewhere"
        link.symlink_to(self.elsewhere)
        self.assertEqual(self.state(link), "no")

    def test_symlinked_root_still_matches(self) -> None:
        link_root = self.tmp / "link-to-workspace"
        link_root.symlink_to(self.workspace)
        self.env_roots = str(link_root)
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.sibling), "no")

    def test_filesystem_root_as_scope_matches_everything(self) -> None:
        self.env_roots = "/"
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_double_slash_root_is_the_filesystem_root(self) -> None:
        # bash's `pwd -P` keeps POSIX's leading `//`, so this root resolves to `//`.
        self.env_roots = "//"
        self.assertEqual(self.state(self.elsewhere), "yes")

    def test_glob_characters_in_the_root_stay_literal(self) -> None:
        starred = self.tmp / "ws*"
        starred.mkdir()
        self.env_roots = str(starred)
        self.assertEqual(self.state(self.tmp / "workspace"), "no")

    def test_explicit_roots_argument_overrides_the_configuration(self) -> None:
        self.assertEqual(self.resolve(str(self.elsewhere), str(self.elsewhere)), "yes")
        self.assertEqual(self.resolve(str(self.repo_a), str(self.elsewhere)), "no")

    def test_empty_roots_argument_falls_back_to_the_configuration(self) -> None:
        self.assertEqual(self.resolve(str(self.repo_a), ""), "yes")
        self.assertEqual(self.resolve(str(self.elsewhere), ""), "no")

    def test_resolver_never_reads_stdin(self) -> None:
        """A guard that drains stdin would starve anything downstream."""
        proc = subprocess.run(
            ["bash", "-c", '. "$0"; avengers_scope_state "$1"; cat',
             str(LIB), str(self.repo_a)],
            input="DOWNSTREAM-PAYLOAD", capture_output=True, text=True,
            timeout=30, check=True, env=self.env())
        self.assertEqual(proc.stdout, "yes\nDOWNSTREAM-PAYLOAD")


class UnresolvableRootTests(ScopeFixture):
    def test_single_unresolvable_root_is_unknown(self) -> None:
        self.env_roots = str(self.tmp / "no-such-root")
        self.assertEqual(self.state(self.repo_a), "unknown")
        self.assertEqual(self.state(self.elsewhere), "unknown")

    def test_unresolvable_root_is_skipped_when_another_resolves(self) -> None:
        self.env_roots = f"{self.tmp / 'no-such-root'}:{self.workspace}"
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_relative_root_is_unresolvable(self) -> None:
        """A relative entry would depend on the hook's cwd, so it is skipped."""
        self.env_roots = "workspace"
        self.assertEqual(self.resolve(str(self.repo_a), cwd=self.tmp), "unknown")

    def test_unreadable_scope_file_is_unknown(self) -> None:
        """A scope that exists but cannot be read is not the same as no scope."""
        (self.config / SCOPE_FILE).mkdir()
        self.assertEqual(self.state(self.repo_a), "unknown")

    def test_dangling_scope_file_symlink_is_unknown(self) -> None:
        (self.config / SCOPE_FILE).symlink_to(self.tmp / "missing-target")
        self.assertEqual(self.state(self.repo_a), "unknown")


class ConfigSourceTests(ScopeFixture):
    def test_env_roots(self) -> None:
        self.env_roots = str(self.workspace)
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_file_roots_under_claude_config_dir(self) -> None:
        self.write_scope_file(f"{self.workspace}\n")
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_file_roots_under_home_when_config_dir_is_unset(self) -> None:
        self.config_dir = None
        self.write_scope_file(f"{self.workspace}\n", self.home / ".claude")
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_config_dir_wins_over_home(self) -> None:
        self.write_scope_file(f"{self.elsewhere}\n", self.home / ".claude")
        self.write_scope_file(f"{self.workspace}\n")
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_env_takes_precedence_over_the_file(self) -> None:
        self.write_scope_file(f"{self.elsewhere}\n")
        self.env_roots = str(self.workspace)
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_empty_env_falls_through_to_the_file(self) -> None:
        self.write_scope_file(f"{self.workspace}\n")
        self.env_roots = ""
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_multiple_env_roots(self) -> None:
        self.env_roots = f"{self.workspace}::{self.elsewhere}:"
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "yes")
        self.assertEqual(self.state(self.sibling), "no")

    def test_multiple_file_roots_with_comments_and_blanks(self) -> None:
        self.write_scope_file(
            "# scoped workspaces\n"
            "\n"
            f"  {self.workspace}  \n"
            "   \n"
            "  # an indented comment\n"
            f"{self.elsewhere}")  # no trailing newline on the last line
        self.assertEqual(self.state(self.repo_a), "yes")
        self.assertEqual(self.state(self.elsewhere), "yes")
        self.assertEqual(self.state(self.sibling), "no")

    def test_commented_out_root_is_ignored(self) -> None:
        self.write_scope_file(f"#{self.elsewhere}\n{self.workspace}\n")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_tilde_expands_in_the_file(self) -> None:
        (self.home / "projects" / "repo-b").mkdir(parents=True)
        self.write_scope_file("~/projects\n")
        self.assertEqual(self.state(self.home / "projects" / "repo-b"), "yes")
        self.assertEqual(self.state(self.home), "no")

    def test_bare_tilde_expands_to_home(self) -> None:
        self.write_scope_file("~\n")
        self.assertEqual(self.state(self.home), "yes")
        self.assertEqual(self.state(self.elsewhere), "no")

    def test_tilde_expands_in_the_env_list(self) -> None:
        (self.home / "projects").mkdir()
        self.env_roots = "~/projects"
        self.assertEqual(self.state(self.home / "projects"), "yes")

    def test_tilde_user_form_is_not_expanded(self) -> None:
        self.write_scope_file("~someone/projects\n")
        self.assertEqual(self.state(self.home), "unknown")


class DefaultDirectoryTests(ScopeFixture):
    """With no dir argument the resolver uses CLAUDE_PROJECT_DIR, then $PWD."""

    def setUp(self) -> None:
        super().setUp()
        self.scope_to_workspace()

    def test_uses_project_dir(self) -> None:
        self.assertEqual(self.resolve(project_dir=str(self.repo_a), cwd=self.elsewhere), "yes")
        self.assertEqual(self.resolve(project_dir=str(self.elsewhere), cwd=self.repo_a), "no")

    def test_falls_back_to_pwd_when_project_dir_is_unset(self) -> None:
        self.assertEqual(self.resolve(cwd=self.repo_a), "yes")
        self.assertEqual(self.resolve(cwd=self.elsewhere), "no")

    def test_falls_back_to_pwd_when_project_dir_is_empty(self) -> None:
        self.assertEqual(self.resolve(project_dir="", cwd=self.repo_a), "yes")


class HookScriptTests(ScopeFixture):
    """End to end: what each hook actually prints in each scope."""

    def setUp(self) -> None:
        super().setUp()
        self.scope_to_workspace()

    def assertOnlyPluginLine(self, out: str) -> None:
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(lines, [EXPECTED_PLUGIN_LINE],
                         f"out-of-scope output was not silent: {out!r}")

    def stripped_copy(self, script: Path) -> Path:
        """The hook without its lib next to it, as after a partial install."""
        stripped = self.tmp / "stripped" / "scripts"
        stripped.mkdir(parents=True)
        shutil.copy(script, stripped / script.name)
        return stripped / script.name

    def run_stripped(self, script: Path) -> str:
        # CLAUDE_PLUGIN_ROOT still points at the real plugin, so the plugin-root
        # line is predictable; only the lib lookup (relative to the script) fails.
        return self.run_hook(self.stripped_copy(script), self.repo_a)

    # -- session-start.sh ------------------------------------------------------

    def test_session_start_in_scope_prints_banner_and_persona(self) -> None:
        out = self.run_hook(SESSION_START, self.repo_a)
        self.assertIn(BANNER, out)
        self.assertIn(PERSONA, out)
        self.assertNotIn(UNKNOWN_NOTE, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_session_start_in_scope_via_the_file(self) -> None:
        self.env_roots = None
        self.write_scope_file(f"{self.workspace}\n")
        out = self.run_hook(SESSION_START, self.repo_a)
        self.assertIn(BANNER, out)
        self.assertIn(PERSONA, out)

    def test_session_start_out_of_scope_prints_only_the_plugin_root(self) -> None:
        self.assertOnlyPluginLine(self.run_hook(SESSION_START, self.elsewhere))

    def test_session_start_sibling_prints_only_the_plugin_root(self) -> None:
        self.assertOnlyPluginLine(self.run_hook(SESSION_START, self.sibling))

    def test_session_start_unset_project_dir_uses_pwd(self) -> None:
        self.assertOnlyPluginLine(
            self.run_hook(SESSION_START, None, cwd=self.elsewhere))
        out = self.run_hook(SESSION_START, None, cwd=self.repo_a)
        self.assertIn(PERSONA, out)

    def test_session_start_unknown_fails_open_for_banner_closed_for_persona(self) -> None:
        out = self.run_hook(SESSION_START, self.tmp / "gone")
        self.assertIn(BANNER, out)
        self.assertIn(UNKNOWN_NOTE, out)
        self.assertNotIn(PERSONA, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_session_start_unresolvable_root_is_unknown(self) -> None:
        self.env_roots = str(self.tmp / "no-such-root")
        out = self.run_hook(SESSION_START, self.repo_a)
        self.assertIn(BANNER, out)
        self.assertIn(UNKNOWN_NOTE, out)
        self.assertNotIn(PERSONA, out)

    def test_session_start_without_the_lib_is_unknown_not_open(self) -> None:
        """A missing resolver must not silently reinstate the persona."""
        out = self.run_stripped(SESSION_START)
        self.assertIn(BANNER, out)
        self.assertIn(UNKNOWN_NOTE, out)
        self.assertNotIn(PERSONA, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    # -- compact-resume.sh -----------------------------------------------------

    def test_compact_resume_in_scope_prints_the_reinjection(self) -> None:
        out = self.run_hook(COMPACT_RESUME, self.repo_a)
        self.assertIn(COMPACT_BODY, out)
        self.assertIn(COMPACT_DISPATCH, out)
        self.assertNotIn(COMPACT_NOTE, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_compact_resume_out_of_scope_prints_only_the_plugin_root(self) -> None:
        """A genuine `no` is silent: no re-injection, and no `unknown` note."""
        self.assertOnlyPluginLine(self.run_hook(COMPACT_RESUME, self.elsewhere))

    def test_compact_resume_sibling_prints_only_the_plugin_root(self) -> None:
        self.assertOnlyPluginLine(self.run_hook(COMPACT_RESUME, self.sibling))

    def test_compact_resume_unknown_fails_closed(self) -> None:
        out = self.run_hook(COMPACT_RESUME, self.tmp / "gone")
        self.assertNotIn(COMPACT_BODY, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_compact_resume_unknown_explains_the_skip(self) -> None:
        """Failing closed is silent, so `unknown` says why - one line, no banner."""
        out = self.run_hook(COMPACT_RESUME, self.tmp / "gone")
        self.assertIn(UNKNOWN_NOTE, out)
        self.assertIn(COMPACT_NOTE, out)
        self.assertNotIn(BANNER, out)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2, f"expected note + plugin-root line: {out!r}")
        self.assertIn(COMPACT_NOTE, lines[0])
        self.assertEqual(lines[1], EXPECTED_PLUGIN_LINE)

    def test_compact_resume_unreadable_scope_file_explains_the_skip(self) -> None:
        self.env_roots = None
        (self.config / SCOPE_FILE).mkdir()
        out = self.run_hook(COMPACT_RESUME, self.repo_a)
        self.assertNotIn(COMPACT_BODY, out)
        self.assertIn(COMPACT_NOTE, out)

    def test_compact_resume_without_the_lib_explains_the_skip(self) -> None:
        """A missing resolver is `unknown` too: no re-injection, but a reason."""
        out = self.run_stripped(COMPACT_RESUME)
        self.assertNotIn(COMPACT_BODY, out)
        self.assertIn(COMPACT_NOTE, out)
        self.assertIn(EXPECTED_PLUGIN_LINE, out)

    def test_compact_resume_unset_project_dir_uses_pwd(self) -> None:
        self.assertOnlyPluginLine(
            self.run_hook(COMPACT_RESUME, None, cwd=self.elsewhere))

    # -- the project-dir line, in scope only -----------------------------------

    def test_project_dir_line_prints_in_scope(self) -> None:
        for script in (SESSION_START, COMPACT_RESUME):
            with self.subTest(script=script.name):
                out = self.run_hook(script, self.repo_a)
                self.assertEqual(
                    [l for l in out.splitlines() if l.startswith(PROJECT_LINE)],
                    [f"{PROJECT_LINE} {self.repo_a}"])

    def test_project_dir_line_is_the_raw_env_value(self) -> None:
        """The guard builds the registry path from CLAUDE_PROJECT_DIR as given, so the
        line must not resolve or rewrite it."""
        link = self.tmp / "repo-link"
        link.symlink_to(self.repo_a)
        out = self.run_hook(SESSION_START, link)
        self.assertIn(f"{PROJECT_LINE} {link}\n", out)

    def test_project_dir_line_absent_outside_scope_or_without_the_env(self) -> None:
        for script in (SESSION_START, COMPACT_RESUME):
            for label, (project_dir, cwd) in {
                    "no": (self.elsewhere, None),
                    "unknown": (self.tmp / "gone", None),
                    "unset": (None, self.repo_a)}.items():
                with self.subTest(script=script.name, state=label):
                    out = self.run_hook(script, project_dir, cwd=cwd)
                    self.assertNotIn(PROJECT_LINE, out)

    # -- the plugin-root line, in every state ----------------------------------

    def test_plugin_root_line_prints_in_every_state(self) -> None:
        cases = {
            "unconfigured": (None, self.elsewhere),
            "yes": (str(self.workspace), self.repo_a),
            "no": (str(self.workspace), self.elsewhere),
            "unknown": (str(self.workspace), self.tmp / "gone"),
        }
        for script in (SESSION_START, COMPACT_RESUME):
            for label, (roots, project_dir) in cases.items():
                with self.subTest(script=script.name, state=label):
                    self.env_roots = roots
                    out = self.run_hook(script, project_dir)
                    self.assertEqual(
                        [l for l in out.splitlines() if l.startswith(PLUGIN_LINE)],
                        [EXPECTED_PLUGIN_LINE])


class HookScriptHygieneTests(unittest.TestCase):
    def test_scripts_parse(self) -> None:
        for script in (LIB, SESSION_START, COMPACT_RESUME):
            with self.subTest(script=script.name):
                proc = subprocess.run(["bash", "-n", str(script)],
                                      capture_output=True, text=True, timeout=30)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_no_hard_coded_scope_root(self) -> None:
        """Roots come from configuration only; the lib ships none of its own."""
        text = LIB.read_text()
        self.assertNotIn("AVENGERS_SCOPE_ROOT=", text)
        self.assertNotRegex(text, r'(?m)^[^#\n]*"/(Users|home)/')


if __name__ == "__main__":
    unittest.main()
