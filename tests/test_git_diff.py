import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.git import get_file_diff

class TestGitDiff(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/mock_project")

    @patch("subprocess.run")
    def test_get_file_diff_unstaged(self, mock_run):
        # Mock unstaged diff
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "diff --git a/file.py b/file.py\nindex ...\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-foo\n+bar"
        mock_run.return_value = mock_result

        diff = get_file_diff(self.project_dir, "file.py", staged=False)

        expected_cmd = ["git", "diff", "--no-color", "--", "file.py"]
        mock_run.assert_called_with(
            expected_cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        self.assertIn("foo", diff)
        self.assertIn("bar", diff)

    @patch("subprocess.run")
    def test_get_file_diff_staged(self, mock_run):
        # Mock staged diff
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "diff --git a/file.py b/file.py..."
        mock_run.return_value = mock_result

        diff = get_file_diff(self.project_dir, "file.py", staged=True)

        expected_cmd = ["git", "diff", "--no-color", "--cached", "--", "file.py"]
        mock_run.assert_called_with(
            expected_cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_get_file_diff_untracked(self, mock_run):
        # Mock empty diff (indicating potentially untracked)
        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 0
        mock_diff_result.stdout = ""

        # Mock ls-files check
        mock_ls_result = MagicMock()
        mock_ls_result.returncode = 0
        mock_ls_result.stdout = "new_file.py"

        # Side effect for subprocess.run to handle multiple calls
        def side_effect(cmd, **kwargs):
            if "diff" in cmd:
                return mock_diff_result
            if "ls-files" in cmd:
                return mock_ls_result
            return MagicMock()

        mock_run.side_effect = side_effect

        # Mock file read
        with patch("pathlib.Path.read_text", return_value="content of new file"):
            diff = get_file_diff(self.project_dir, "new_file.py", staged=False)

            self.assertIn("content of new file", diff)
            self.assertIn("--- /dev/null", diff)
            self.assertIn("+++ b/new_file.py", diff)

if __name__ == "__main__":
    unittest.main()
