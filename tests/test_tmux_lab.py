import unittest
from unittest.mock import MagicMock, patch
import sys
import subprocess

# Ensure we can import shared.tmux_lab
sys.path.insert(0, ".")
from shared.tmux_lab import TmuxManager

class TestTmuxLab(unittest.TestCase):
    def setUp(self):
        # Mock shutil.which to simulate tmux is installed
        self.which_patcher = patch('shutil.which')
        self.mock_which = self.which_patcher.start()
        self.mock_which.return_value = "/usr/bin/tmux"

        # Mock subprocess.run
        self.run_patcher = patch('subprocess.run')
        self.mock_run = self.run_patcher.start()

        self.manager = TmuxManager()

    def tearDown(self):
        self.which_patcher.stop()
        self.run_patcher.stop()

    def test_init_no_tmux(self):
        self.mock_which.return_value = None
        manager = TmuxManager()
        self.assertIsNone(manager.tmux_path)

    def test_list_sessions_success(self):
        self.mock_run.return_value = MagicMock(
            returncode=0,
            stdout="session1:2:2023-01-01:1\nsession2:1:2023-01-02:0\n"
        )
        sessions = self.manager.list_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertEqual(sessions[0]['name'], 'session1')
        self.assertTrue(sessions[0]['attached'])
        self.assertEqual(sessions[1]['name'], 'session2')
        self.assertFalse(sessions[1]['attached'])

        expected_cmd = ["/usr/bin/tmux", "list-sessions", "-F", "#{session_name}:#{session_windows}:#{session_created}:#{session_attached}"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

    def test_list_sessions_empty(self):
        self.mock_run.return_value = MagicMock(returncode=1, stderr="no server running")
        sessions = self.manager.list_sessions()
        self.assertEqual(sessions, [])

    def test_new_session(self):
        self.mock_run.return_value = MagicMock(returncode=0)
        success = self.manager.new_session("mysession", "top")
        self.assertTrue(success)

        expected_cmd = ["/usr/bin/tmux", "new-session", "-d", "-s", "mysession", "top"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

    def test_kill_session(self):
        self.mock_run.return_value = MagicMock(returncode=0)
        success = self.manager.kill_session("mysession")
        self.assertTrue(success)

        expected_cmd = ["/usr/bin/tmux", "kill-session", "-t", "mysession"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

    def test_send_keys(self):
        self.mock_run.return_value = MagicMock(returncode=0)
        success = self.manager.send_keys("mysession", "ls")
        self.assertTrue(success)

        expected_cmd = ["/usr/bin/tmux", "send-keys", "-t", "mysession", "ls", "C-m"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

    def test_capture_pane(self):
        self.mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2")
        output = self.manager.capture_pane("mysession", lines=10)
        self.assertEqual(output, "line1\nline2")

        expected_cmd = ["/usr/bin/tmux", "capture-pane", "-p", "-t", "mysession", "-S", "-10"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

    def test_list_windows(self):
        self.mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0:bash:1\n1:vim:0\n"
        )
        windows = self.manager.list_windows("mysession")
        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0]['name'], 'bash')
        self.assertTrue(windows[0]['active'])
        self.assertEqual(windows[1]['name'], 'vim')
        self.assertFalse(windows[1]['active'])

    def test_new_window(self):
        self.mock_run.return_value = MagicMock(returncode=0)
        success = self.manager.new_window("mysession", "newwin", "htop")
        self.assertTrue(success)

        expected_cmd = ["/usr/bin/tmux", "new-window", "-t", "mysession", "-n", "newwin", "htop"]
        self.mock_run.assert_called_with(expected_cmd, capture_output=True, text=True, check=False)

if __name__ == '__main__':
    unittest.main()
