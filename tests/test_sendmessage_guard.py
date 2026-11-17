"""Tests for the paired-reviewer SendMessage guard (stdlib unittest).

The guard is the runtime enforcement of the Paired Reviewers rule in
`.claude/rules/ironman-delegation.md`: a PreToolUse hook on SendMessage that
restricts subagents only. A payload with no `agent_id` is a main-session call and
is allowed. A subagent registered in `<project>/.avengers/pairs.json` may message
`main` and its own partner; any other subagent only `main`. Covers:

1. `scripts/sendmessage-guard.sh` end to end, fed a hook payload on stdin: allowed
   calls exit 0, denied ones exit 2 with a reason on stderr.
2. Fail closed for subagents: no registry, an unreadable or malformed one, no
   CLAUDE_PROJECT_DIR or a malformed agent_id leave only `main`; a payload that
   is not a JSON object, or a guard that cannot run, is denied - never an exit
   other than 0 or 2.
3. The AVENGERS_PAIR_GUARD_LOG debug line (payload keys only).
4. `pair-registry.py register|unregister|list`, the commands IronMan runs.
5. The hook is wired in `hooks/hooks.json`.

Every subprocess gets HOME and CLAUDE_PROJECT_DIR pointed into a tmpdir.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD_HOOK = ROOT / "scripts" / "sendmessage-guard.sh"
REGISTRY_SCRIPT = ROOT / "scripts" / "pair-registry.py"
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
HOOK_COMMAND = 'bash "${CLAUDE_PLUGIN_ROOT}/scripts/sendmessage-guard.sh"'

THOR_ID = "a1b2c3d4e5f6-thor"
CAPTAIN_ID = "a9f8e7d6c5b4-captain"
THOR_B_ID = "b1b2c3d4e5f6-thor"
CAPTAIN_B_ID = "b9f8e7d6c5b4-captain"
LONE_ID = "c0c0c0c0c0c0-blackwidow"
ALLOW, DENY = 0, 2
MAIN_SESSION = object()  # sentinel: build a payload with no agent_id


def payload(to: object, sender: object = MAIN_SESSION, tool: str = "SendMessage",
            **extra: object) -> str:
    data = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {"to": to, "message": "round 1 review request"}, **extra}
    if sender is not MAIN_SESSION:
        data["agent_id"] = sender
    return json.dumps(data)


class GuardFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.registry = self.project / ".avengers" / "pairs.json"

    def env(self, project_dir: Path | None = None, **extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_PROJECT_DIR", "AVENGERS_PAIR_GUARD_LOG")}
        env["HOME"] = str(self.tmp)
        if project_dir is not None:
            env["CLAUDE_PROJECT_DIR"] = str(project_dir)
        env.update(extra)
        return env

    def hook(self, stdin: str, project_dir: Path | None = None,
             env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(GUARD_HOOK)], input=stdin, capture_output=True,
                              text=True, timeout=30, check=False, cwd=str(self.tmp),
                              env=env or self.env(project_dir or self.project))

    def registry_cmd(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(REGISTRY_SCRIPT), *args,
                               "--project-dir", str(self.project)],
                              capture_output=True, text=True, timeout=30, check=False,
                              cwd=str(self.tmp), env=self.env())

    def write_registry(self, data: object) -> None:
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        self.registry.write_text(data if isinstance(data, str) else json.dumps(data))

    def register_pairs(self) -> None:
        self.write_registry({"version": 1, "pairs": {
            "team-a": {"thor": THOR_ID, "captain": CAPTAIN_ID},
            "team-b": {"thor": THOR_B_ID, "captain": CAPTAIN_B_ID}}})

    def assertDecision(self, proc: subprocess.CompletedProcess, code: int) -> None:
        self.assertEqual(proc.returncode, code, f"stderr:\n{proc.stderr}")
        if code == DENY:
            self.assertIn("SendMessage denied", proc.stderr)


class MainSessionTests(GuardFixture):
    """No agent_id: the orchestrator itself, never restricted."""

    def test_main_session_may_message_any_target(self) -> None:
        self.register_pairs()
        for target in ("worker", "worker [3fa9c1]", "a0000000-unpaired", THOR_ID, "main"):
            with self.subTest(to=target):
                self.assertDecision(self.hook(payload(target)), ALLOW)

    def test_main_session_without_a_registry(self) -> None:
        self.assertDecision(self.hook(payload("a0000000-unpaired")), ALLOW)
        self.assertDecision(self.hook(payload("worker"), env=self.env(None)), ALLOW)

    def test_agent_type_without_agent_id_is_main(self) -> None:
        """A `claude --agent <name>` session sets agent_type but is the main thread."""
        self.register_pairs()
        proc = self.hook(payload("a0000000-unpaired", agent_type="avengers-dev:thor"))
        self.assertDecision(proc, ALLOW)

    def test_other_tools_pass_through(self) -> None:
        self.assertDecision(self.hook(payload("anything", sender=THOR_ID, tool="Bash")), ALLOW)


class SubagentTests(GuardFixture):
    def test_registered_agent_may_message_main_and_own_partner(self) -> None:
        self.register_pairs()
        for sender, target in ((THOR_ID, "main"), (THOR_ID, CAPTAIN_ID),
                               (CAPTAIN_ID, THOR_ID), (CAPTAIN_B_ID, THOR_B_ID)):
            with self.subTest(sender=sender, to=target):
                self.assertDecision(self.hook(payload(target, sender=sender)), ALLOW)

    def test_registered_agent_may_not_message_another_team(self) -> None:
        self.register_pairs()
        for sender, target in ((THOR_ID, CAPTAIN_B_ID), (THOR_ID, THOR_B_ID),
                               (CAPTAIN_B_ID, CAPTAIN_ID), (THOR_ID, THOR_ID)):
            with self.subTest(sender=sender, to=target):
                proc = self.hook(payload(target, sender=sender))
                self.assertDecision(proc, DENY)
                self.assertIn("not the sender's registered partner", proc.stderr)

    def test_unregistered_subagent_may_message_only_main(self) -> None:
        self.register_pairs()
        self.assertDecision(self.hook(payload("main", sender=LONE_ID)), ALLOW)
        for target in (THOR_ID, CAPTAIN_ID, "worker"):
            with self.subTest(to=target):
                proc = self.hook(payload(target, sender=LONE_ID))
                self.assertDecision(proc, DENY)
                self.assertIn("no registered partner", proc.stderr)

    def test_partner_not_yet_registered(self) -> None:
        """While only the Captain is registered, it may message only `main`."""
        self.write_registry({"version": 1, "pairs": {"team-a": {"captain": CAPTAIN_ID}}})
        self.assertDecision(self.hook(payload("main", sender=CAPTAIN_ID)), ALLOW)
        self.assertDecision(self.hook(payload(THOR_ID, sender=CAPTAIN_ID)), DENY)

    def test_session_and_agent_names_are_denied(self) -> None:
        self.register_pairs()
        for name in ("worker", "researcher", "captain", "thor", "ironman", "Main"):
            with self.subTest(to=name):
                self.assertDecision(self.hook(payload(name, sender=THOR_ID)), DENY)

    def test_name_with_ref_is_denied_first(self) -> None:
        """`name [ref]` addresses another session, even when the name part is the
        sender's own partner or `main`."""
        self.register_pairs()
        for target in ("worker [3fa9c1]", f"{CAPTAIN_ID} [3fa9c1]", f"{CAPTAIN_ID}[x]",
                       "two words", f" {CAPTAIN_ID}", f"{CAPTAIN_ID}\n", "main [3fa9c1]"):
            with self.subTest(to=target):
                proc = self.hook(payload(target, sender=THOR_ID))
                self.assertDecision(proc, DENY)
                self.assertIn("whitespace or `[`", proc.stderr)

    def test_lookalike_and_invisible_targets_are_denied(self) -> None:
        """A target that only looks like `main` or the partner's id is not it."""
        self.register_pairs()
        cyrillic_a, zero_width, nbsp = "\u0430", "\u200b", "\u00a0"
        for target in ("m" + cyrillic_a + "in", "main" + zero_width, zero_width + "main",
                       CAPTAIN_ID.replace("a", cyrillic_a, 1), CAPTAIN_ID + zero_width,
                       CAPTAIN_ID[:4] + "\u200d" + CAPTAIN_ID[4:], CAPTAIN_ID + "\ufeff",
                       CAPTAIN_ID + nbsp, "\uff4d\uff41\uff49\uff4e",  # fullwidth "main"
                       CAPTAIN_ID.upper()):
            with self.subTest(to=ascii(target)):
                self.assertDecision(self.hook(payload(target, sender=THOR_ID)), DENY)

    def test_lookalike_sender_is_not_the_registered_agent(self) -> None:
        self.register_pairs()
        for sender in (THOR_ID.replace("a", "\u0430", 1), THOR_ID + "\u200b"):
            with self.subTest(sender=ascii(sender)):
                self.assertDecision(self.hook(payload(CAPTAIN_ID, sender=sender)), DENY)
                self.assertDecision(self.hook(payload("main", sender=sender)), ALLOW)

    def test_bad_targets_are_denied(self) -> None:
        self.register_pairs()
        for target in ("", None, 42, [CAPTAIN_ID], {"id": CAPTAIN_ID}):
            with self.subTest(to=target):
                self.assertDecision(self.hook(payload(target, sender=THOR_ID)), DENY)


class GuardFailClosedTests(GuardFixture):
    def assertOnlyMain(self, sender: object = THOR_ID,
                       env: dict[str, str] | None = None) -> None:
        self.assertDecision(self.hook(payload("main", sender=sender), env=env), ALLOW)
        for target in (CAPTAIN_ID, THOR_B_ID, "worker"):
            with self.subTest(to=target):
                self.assertDecision(self.hook(payload(target, sender=sender), env=env), DENY)

    def test_no_registry_allows_only_main(self) -> None:
        self.assertFalse(self.registry.exists())
        self.assertOnlyMain()

    def test_malformed_registry_allows_only_main(self) -> None:
        cases = {
            "not json": "{",
            "wrong version": {"version": 2, "pairs": {"t": {"thor": THOR_ID,
                                                            "captain": CAPTAIN_ID}}},
            "pairs not an object": {"version": 1, "pairs": [THOR_ID, CAPTAIN_ID]},
            "extra role": {"version": 1, "pairs": {"t": {"thor": THOR_ID,
                                                         "captain": CAPTAIN_ID, "hulk": "a1"}}},
            "id with a space": {"version": 1, "pairs": {
                "t": {"thor": THOR_ID, "captain": CAPTAIN_ID},
                "u": {"thor": "x [ref]"}}},
            "bad team name": {"version": 1, "pairs": {"a team": {"thor": THOR_ID,
                                                                 "captain": CAPTAIN_ID}}},
            "top level list": [THOR_ID, CAPTAIN_ID],
        }
        for name, data in cases.items():
            with self.subTest(case=name):
                self.write_registry(data)
                self.assertOnlyMain()

    def test_unreadable_registry_allows_only_main(self) -> None:
        self.register_pairs()
        self.registry.chmod(0)
        self.addCleanup(self.registry.chmod, 0o600)
        if os.access(self.registry, os.R_OK):
            self.skipTest("running as a user that can read a mode-000 file")
        self.assertOnlyMain()

    def test_registry_is_a_directory(self) -> None:
        self.registry.mkdir(parents=True)
        self.assertOnlyMain()

    def test_no_project_dir_allows_only_main(self) -> None:
        self.register_pairs()
        self.assertOnlyMain(env=self.env(None))

    def test_malformed_payload_with_agent_id_allows_only_main(self) -> None:
        self.register_pairs()
        for sender in ("", None, 7, "x [ref]", ["a"]):
            with self.subTest(sender=sender):
                self.assertOnlyMain(sender=sender)
        # A subagent payload without a usable tool_input has no target: denied.
        for tool_input in (None, "main", [], {}):
            with self.subTest(tool_input=tool_input):
                stdin = json.dumps({"tool_name": "SendMessage", "agent_id": THOR_ID,
                                    "tool_input": tool_input})
                self.assertDecision(self.hook(stdin), DENY)

    def test_unparsable_payload_is_denied(self) -> None:
        """Not a JSON object: the sender cannot be shown to be the main session."""
        self.register_pairs()
        for stdin in ("", "not json", "[]", '"main"'):
            with self.subTest(stdin=stdin):
                self.assertDecision(self.hook(stdin), DENY)

    def test_guard_that_cannot_run_denies(self) -> None:
        """A crash or a missing interpreter is exit 2, never a non-blocking error."""
        self.register_pairs()
        fake_bin = self.tmp / "bin"
        fake_bin.mkdir()
        broken = fake_bin / "python3"
        broken.write_text("#!/bin/sh\nexit 1\n")
        broken.chmod(0o755)
        env = self.env(self.project, PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
        for stdin in (payload("main", sender=THOR_ID), payload(CAPTAIN_ID, sender=THOR_ID)):
            with self.subTest(stdin=stdin):
                proc = self.hook(stdin, env=env)
                self.assertDecision(proc, DENY)
                self.assertIn("fails closed", proc.stderr)


class GuardDebugLogTests(GuardFixture):
    def test_log_records_keys_not_values(self) -> None:
        log = self.tmp / "guard.log"
        env = self.env(self.project, AVENGERS_PAIR_GUARD_LOG=str(log))
        self.hook(payload("main", agent_type="avengers-dev:thor"), env=env)
        self.hook(payload("main", sender=THOR_ID), env=env)
        lines = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual([line["has_agent_id"] for line in lines], [False, True])
        self.assertEqual(lines[0]["agent_type"], "avengers-dev:thor")
        self.assertIn("tool_input", lines[0]["keys"])
        self.assertNotIn(THOR_ID, log.read_text())
        self.assertNotIn("round 1 review request", log.read_text())

    def test_unwritable_log_does_not_change_the_decision(self) -> None:
        env = self.env(self.project, AVENGERS_PAIR_GUARD_LOG=str(self.tmp / "no" / "x.log"))
        self.assertDecision(self.hook(payload("main", sender=THOR_ID), env=env), ALLOW)


class RegistryCommandTests(GuardFixture):
    def test_dispatch_order_registers_both_sides(self) -> None:
        """Captain first, then its Thor: each id is allowed once registered."""
        proc = self.registry_cmd("register", "--team", "team-a", "--captain", CAPTAIN_ID)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertDecision(self.hook(payload(CAPTAIN_ID, sender=THOR_ID)), DENY)
        proc = self.registry_cmd("register", "--team", "team-a", "--thor", THOR_ID)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["pairs"],
                         {"team-a": {"thor": THOR_ID, "captain": CAPTAIN_ID}})
        self.assertDecision(self.hook(payload(CAPTAIN_ID, sender=THOR_ID)), ALLOW)
        self.assertDecision(self.hook(payload(THOR_ID, sender=CAPTAIN_ID)), ALLOW)

    def test_unregister_revokes(self) -> None:
        self.register_pairs()
        proc = self.registry_cmd("unregister", "--team", "team-a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(list(json.loads(proc.stdout)["pairs"]), ["team-b"])
        self.assertDecision(self.hook(payload(CAPTAIN_ID, sender=THOR_ID)), DENY)
        # Unregistering an absent team is a no-op, not an error.
        self.assertEqual(self.registry_cmd("unregister", "--team", "gone").returncode, 0)

    def test_parallel_registers_all_land(self) -> None:
        """Read-modify-write is serialised: no register is lost to a race."""
        teams = [f"team-{i:02d}" for i in range(20)]
        with ThreadPoolExecutor(max_workers=len(teams)) as pool:
            procs = list(pool.map(lambda i: self.registry_cmd(
                "register", "--team", teams[i], "--thor", f"t{i:02d}-thor",
                "--captain", f"c{i:02d}-captain"), range(len(teams))))
        for proc in procs:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        pairs = json.loads(self.registry.read_text())["pairs"]
        self.assertEqual(sorted(pairs), teams)
        self.assertEqual(pairs["team-07"], {"thor": "t07-thor", "captain": "c07-captain"})

    def test_register_racing_unregister(self) -> None:
        """Unregisters of old teams and registers of new ones, interleaved: every new
        team is present and every old one is gone."""
        old = [f"old-{i:02d}" for i in range(10)]
        new = [f"new-{i:02d}" for i in range(10)]
        self.write_registry({"version": 1, "pairs": {
            team: {"thor": f"{team}-thor"} for team in old}})
        jobs = [("unregister", "--team", team) for team in old]
        jobs += [("register", "--team", team, "--thor", f"{team}-thor") for team in new]
        jobs = [job for pair in zip(jobs[:10], jobs[10:]) for job in pair]
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            procs = list(pool.map(lambda job: self.registry_cmd(*job), jobs))
        for proc in procs:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(sorted(json.loads(self.registry.read_text())["pairs"]), new)

    def test_lock_file_sits_beside_the_registry(self) -> None:
        self.registry_cmd("register", "--team", "team-a", "--thor", THOR_ID)
        self.assertTrue((self.project / ".avengers" / "pairs.lock").exists())

    def test_register_rejects_bad_input(self) -> None:
        for args in (("--team", "team-a"),
                     ("--team", "team-a", "--thor", "worker [3fa9c1]"),
                     ("--team", "a team", "--thor", THOR_ID)):
            with self.subTest(args=args):
                self.assertNotEqual(self.registry_cmd("register", *args).returncode, 0)
        self.assertFalse(self.registry.exists())

    def test_an_id_belongs_to_one_team(self) -> None:
        self.register_pairs()
        proc = self.registry_cmd("register", "--team", "team-c", "--thor", THOR_ID)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("already registered to team team-a", proc.stderr)

    def test_register_refuses_a_malformed_registry(self) -> None:
        self.write_registry("{")
        proc = self.registry_cmd("register", "--team", "team-a", "--thor", THOR_ID)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.registry.read_text(), "{")

    def test_list_and_help(self) -> None:
        proc = self.registry_cmd("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {"version": 1, "pairs": {}})
        proc = subprocess.run([sys.executable, str(REGISTRY_SCRIPT), "--help"],
                              capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("guard", proc.stdout)


class HookWiringTests(unittest.TestCase):
    def test_missing_script_cannot_fail_closed(self) -> None:
        """Documents a limit, not a feature: bash exits 127 on a missing script, which
        Claude Code treats as non-blocking, so the README must say so."""
        proc = subprocess.run(["bash", str(ROOT / "scripts" / "no-such-guard.sh")],
                              input=payload("worker", sender=THOR_ID), capture_output=True,
                              text=True, timeout=30, check=False)
        self.assertEqual(proc.returncode, 127)
        self.assertIn("exit 127", (ROOT / "README.md").read_text())

    def test_pretooluse_hook_guards_sendmessage(self) -> None:
        hooks = json.loads(HOOKS_JSON.read_text())["hooks"]["PreToolUse"]
        commands = [h["command"] for entry in hooks if entry.get("matcher") == "SendMessage"
                    for h in entry["hooks"]]
        self.assertEqual(commands, [HOOK_COMMAND])

    def test_hook_scripts_are_executable(self) -> None:
        for script in (GUARD_HOOK, REGISTRY_SCRIPT):
            with self.subTest(script=script.name):
                self.assertTrue(os.access(script, os.X_OK))


if __name__ == "__main__":
    unittest.main()
