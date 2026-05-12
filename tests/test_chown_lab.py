import unittest
import sys
import os
import shutil
import tempfile
import argparse
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module to test.
sys.path.append(str(Path(__file__).parent.parent))

from shared.chown_lab import ChownManager, run_chown_lab_logic
from main import run_chown_lab

class TestChownLab(unittest.TestCase):
    def setUp(self):
        self.manager = ChownManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_file.txt"
        self.test_file.write_text("content")
        # Ensure we have pwd/grp for this test
        if not self.manager.have_pwd:
            self.skipTest("pwd/grp modules not available on this platform")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_manager_get_uid_gid(self):
        # We assume root (0) exists on unix test systems
        uid = self.manager.get_uid("root")
        self.assertEqual(uid, 0)

        # Test numeric parsing
        uid_num = self.manager.get_uid("1000")
        self.assertEqual(uid_num, 1000)

        gid_num = self.manager.get_gid("1000")
        self.assertEqual(gid_num, 1000)

    def test_manager_get_ownership(self):
        res = self.manager.get_ownership(str(self.test_file))
        self.assertNotIn("error", res)
        self.assertIn("uid", res)
        self.assertIn("gid", res)
        self.assertIn("user", res)
        self.assertIn("group", res)

    @patch('os.chown')
    def test_manager_set_ownership(self, mock_chown):
        success = self.manager.set_ownership(str(self.test_file), "root:root")
        self.assertTrue(success)
        mock_chown.assert_called_once()
        args, _ = mock_chown.call_args
        self.assertEqual(args[0], Path(self.test_file))
        self.assertEqual(args[1], 0) # root uid

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_check(self, mock_stdout):
        args = MagicMock()
        args.action = "check"
        args.file = str(self.test_file)

        with self.assertRaises(SystemExit) as cm:
            run_chown_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("File:", output)
        self.assertIn("Ownership:", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_list_users(self, mock_stdout):
        args = MagicMock()
        args.action = "list"
        args.type = "users"

        with self.assertRaises(SystemExit) as cm:
            run_chown_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("UID", output)
        self.assertIn("User", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_list_groups(self, mock_stdout):
        args = MagicMock()
        args.action = "list"
        args.type = "groups"

        with self.assertRaises(SystemExit) as cm:
            run_chown_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("GID", output)
        self.assertIn("Group", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_chown_lab_tui(self, mock_stdout):
        args = argparse.Namespace(action="tui", project_dir=Path("."))

        with patch('shared.tui.AgentTUI') as mock_agent_tui:
            mock_app = MagicMock()
            mock_agent_tui.return_value = mock_app

            with self.assertRaises(SystemExit) as cm:
                run_chown_lab(args)

            self.assertEqual(cm.exception.code, 0)
            mock_agent_tui.assert_called_once_with(project_dir=Path("."), start_tab="tab-chown")
            mock_app.run.assert_called_once()
            self.assertIn("Launching Chown Lab TUI...", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
