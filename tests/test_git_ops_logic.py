import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.git import get_git_status, stage_file, unstage_file, commit_changes, discard_changes, pull_changes

class TestGitOpsLogic(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")

    @patch("subprocess.run")
    def test_get_git_status(self, mock_run):
        # Mock porcelain output
        # M  file1.py (Staged)
        #  M file2.py (Unstaged)
        # ?? new.py   (Untracked)
        mock_output = "M  file1.py\n M file2.py\n?? new.py\n"

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        files = get_git_status(self.project_dir)

        self.assertEqual(len(files), 3)

        self.assertEqual(files[0]["path"], "file1.py")
        self.assertEqual(files[0]["status_code"], "M ")
        self.assertTrue(files[0]["staged"])

        self.assertEqual(files[1]["path"], "file2.py")
        self.assertEqual(files[1]["status_code"], " M")
        self.assertFalse(files[1]["staged"])

        self.assertEqual(files[2]["path"], "new.py")
        self.assertEqual(files[2]["status_code"], "??")
        self.assertFalse(files[2]["staged"]) # ?? counts as unstaged for our UI toggle

    @patch("subprocess.run")
    def test_stage_file(self, mock_run):
        stage_file(self.project_dir, "file.py")
        mock_run.assert_called_with(["git", "add", "file.py"], cwd=self.project_dir, check=True, stdout=-1, stderr=-1)

    @patch("subprocess.run")
    def test_unstage_file(self, mock_run):
        unstage_file(self.project_dir, "file.py")
        mock_run.assert_called_with(["git", "restore", "--staged", "file.py"], cwd=self.project_dir, check=True, stdout=-1, stderr=-1)

    @patch("subprocess.run")
    def test_commit_changes(self, mock_run):
        commit_changes(self.project_dir, "feat: logic")
        mock_run.assert_called_with(["git", "commit", "-m", "feat: logic"], cwd=self.project_dir, check=True, stdout=-1, stderr=-1)

    @patch("subprocess.run")
    def test_pull_changes(self, mock_run):
        pull_changes(self.project_dir)
        mock_run.assert_called_with(["git", "pull"], cwd=self.project_dir, check=True, stdout=-1, stderr=-1)

    @patch("shared.git.run_git")
    def test_discard_changes(self, mock_run_git):
        # Setup: first call fails (restore), second call succeeds (clean)
        mock_run_git.side_effect = [False, True]

        result = discard_changes(self.project_dir, "file.py")

        self.assertTrue(result)
        # Verify calls
        from unittest.mock import call
        expected_calls = [
            call(["restore", "file.py"], self.project_dir),
            call(["clean", "-f", "file.py"], self.project_dir)
        ]
        mock_run_git.assert_has_calls(expected_calls)

if __name__ == "__main__":
    unittest.main()
