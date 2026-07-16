import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys
import os

sys.path.append(os.getcwd())
from shared.crontab_lab import CrontabLabManager

class TestCrontabLabManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_dir = Path(self.temp_dir.name)
        self.manager = CrontabLabManager(backup_dir=self.backup_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('shared.crontab_lab.subprocess.run')
    def test_read_crontab(self, mock_run):
        # Mock success
        mock_result = MagicMock()
        mock_result.stdout = "* * * * * echo 'Hello'\n"
        mock_run.return_value = mock_result

        content = self.manager.read_crontab()
        self.assertEqual(content, "* * * * * echo 'Hello'")
        mock_run.assert_called_with(["crontab", "-l"], capture_output=True, text=True, check=True)

    @patch('shared.crontab_lab.subprocess.run')
    def test_read_crontab_empty(self, mock_run):
        # Mock "no crontab for user" exception
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, ["crontab", "-l"], stderr="no crontab for testuser")

        content = self.manager.read_crontab()
        self.assertEqual(content, "")

    @patch('shared.crontab_lab.subprocess.Popen')
    def test_write_crontab(self, mock_popen):
        # Mock success
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.manager.write_crontab("* * * * * echo 'Test'")
        self.assertTrue(result)
        mock_popen.assert_called_with(
            ["crontab", "-"],
            stdin=-1, # subprocess.PIPE
            stdout=-1,
            stderr=-1
        )
        # Verify newline was added
        mock_process.communicate.assert_called_with(input=b"* * * * * echo 'Test'\n")

    @patch('shared.crontab_lab.subprocess.run')
    def test_clear_crontab(self, mock_run):
        # Mock success
        self.manager.clear_crontab()
        mock_run.assert_called_with(["crontab", "-r"], capture_output=True, text=True, check=True)

    @patch('shared.crontab_lab.CrontabLabManager.read_crontab')
    def test_backup_crontab(self, mock_read):
        mock_read.return_value = "* * * * * test backup"
        filepath = self.manager.backup_crontab()

        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.startswith(str(self.backup_dir)))

        with open(filepath, "r") as f:
            self.assertEqual(f.read(), "* * * * * test backup")

    @patch('shared.crontab_lab.CrontabLabManager.write_crontab')
    def test_restore_crontab(self, mock_write):
        test_file = self.backup_dir / "test_backup.txt"
        test_file.write_text("* * * * * test restore")

        mock_write.return_value = True

        result = self.manager.restore_crontab(str(test_file))
        self.assertTrue(result)
        mock_write.assert_called_with("* * * * * test restore")

if __name__ == '__main__':
    unittest.main()
