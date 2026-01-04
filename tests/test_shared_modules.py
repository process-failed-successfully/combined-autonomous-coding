import unittest
from unittest.mock import patch
import time
import subprocess
import logging
from pathlib import Path
from shared.agent_client import AgentClient
from shared.state import StateManager
from shared.logger import setup_logger
from shared.git import run_git, ensure_git_safe


class TestSharedModules(unittest.TestCase):

    # --- AgentClient Tests ---

    @patch("requests.post")
    def test_agent_client_heartbeat(self, mock_post):
        # Mock thread start to avoid running background thread if possible,
        # or we just let it run and stop it.
        # But AgentClient starts thread in __init__.
        # We'll stop it immediately.
        client = AgentClient("test_id", "http://test")
        client.stop()

        # Manually call _do_report_state
        client._do_report_state({"foo": "bar"})
        mock_post.assert_called_with(
            "http://test/api/agents/test_id/heartbeat", json={"foo": "bar"}, timeout=2
        )

    @patch("requests.post")
    def test_agent_client_report_state(self, mock_post):
        client = AgentClient("test_id", "http://test")
        client.stop()

        client.report_state(status="running")
        # Since it uses executor, we need to wait a bit or mock executor
        # The executor is a ThreadPoolExecutor.
        # We can just wait a tiny bit.
        time.sleep(0.1)

        mock_post.assert_called()

    @patch("requests.get")
    def test_agent_client_poll_commands(self, mock_get):
        client = AgentClient("test_id", "http://test")
        client.stop()

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"commands": ["pause", "skip"]}

        control = client.poll_commands()
        self.assertTrue(control.pause_requested)
        self.assertTrue(control.skip_requested)

        client.clear_skip()
        self.assertFalse(client.local_control.skip_requested)

    def test_agent_client_apply_command(self):
        client = AgentClient("test_id", "http://test")
        client.stop()

        client._apply_command("stop")
        self.assertTrue(client.local_control.stop_requested)

        client._apply_command("resume")
        self.assertFalse(client.local_control.pause_requested)

    # --- State Tests ---

    def test_state_manager(self):
        sm = StateManager()
        sm.update_state(iteration=5, current_task="Coding")

        s = sm.get_state()
        self.assertEqual(s["iteration"], 5)
        self.assertEqual(s["current_task"], "Coding")
        self.assertGreater(s["last_update_ts"], 0)

        sm.request_stop()
        ctrl = sm.check_control()
        self.assertTrue(ctrl.stop_requested)

        sm.request_pause()
        self.assertTrue(sm.is_paused())

        sm.request_resume()
        self.assertFalse(sm.is_paused())

        sm.request_skip()
        ctrl = sm.check_control()
        self.assertTrue(ctrl.skip_requested)

        sm.clear_skip()
        ctrl = sm.check_control()
        self.assertFalse(ctrl.skip_requested)

    # --- Logger Tests ---

    def test_setup_logger(self):
        # We can't easily test stdout content without capturing it,
        # but we can verify logger configuration.
        logger, handler = setup_logger("test_logger", verbose=True)
        self.assertTrue(logger.hasHandlers())
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertIsNotNone(handler)

        # Test idempotency
        logger2, handler2 = setup_logger("test_logger")
        self.assertEqual(logger, logger2)
        self.assertEqual(handler, handler2)

        # Test file handler - skipping due to mocking difficulties in this
        # context

    # --- Git Tests ---

    @patch("subprocess.run")
    def test_run_git_success(self, mock_run):
        mock_run.return_value.returncode = 0
        res = run_git(["status"], Path("."))
        self.assertTrue(res)

    @patch("subprocess.run")
    def test_run_git_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git"], stderr=b"error"
        )
        res = run_git(["status"], Path("."))
        self.assertFalse(res)

    @patch("shared.git.run_git")
    def test_ensure_git_safe_new_repo(self, mock_run_git):
        p = Path("/tmp/test_git_repo")
        with patch.object(Path, "exists") as mock_exists:
            # Simulate .git does not exist
            mock_exists.return_value = False

            # We assume mock_run_git returns True
            mock_run_git.return_value = True

            ensure_git_safe(p)

            # verify init, add, commit, branch calls
            self.assertTrue(mock_run_git.call_count >= 4)
            mock_run_git.assert_any_call(["init"], p)

    @patch("shared.git.run_git")
    def test_ensure_git_safe_existing_repo(self, mock_run_git):
        p = Path("/tmp/test_git_repo")
        with patch.object(Path, "exists") as mock_exists:
            # Simulate .git exists
            mock_exists.return_value = True
            mock_run_git.return_value = True

            ensure_git_safe(p)

            # Verify only checkout
            mock_run_git.assert_called_once()
            args = mock_run_git.call_args[0][0]
            self.assertEqual(args[0], "checkout")

    @patch("subprocess.run")
    @patch("shared.git.run_git")
    def test_push_branch_blocks_main(self, mock_run_git, mock_sub_run):
        # Simulate current branch is main
        mock_sub_run.return_value.stdout = "main\n"
        mock_sub_run.return_value.returncode = 0

        from shared.git import push_branch
        res = push_branch(Path("/tmp/fake_repo"))

        self.assertFalse(res)
        # Verify run_git was NOT called for push
        mock_run_git.assert_not_called()

    @patch("subprocess.run")
    @patch("shared.git.run_git")
    def test_push_branch_allows_non_main(self, mock_run_git, mock_sub_run):
        # Simulate current branch is agent/PROJ-123
        mock_sub_run.return_value.stdout = "agent/PROJ-123\n"
        mock_sub_run.return_value.returncode = 0
        mock_run_git.return_value = True

        from shared.git import push_branch
        res = push_branch(Path("/tmp/fake_repo"))

        self.assertTrue(res)
        # Verify run_git WAS called for push
        mock_run_git.assert_called_with(["push", "-u", "origin", "agent/PROJ-123"], Path("/tmp/fake_repo"))


if __name__ == "__main__":
    unittest.main()
