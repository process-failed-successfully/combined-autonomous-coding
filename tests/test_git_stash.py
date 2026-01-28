import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.git import get_git_stash_list, get_stash_show, stash_push, stash_pop, stash_drop, stash_apply

class TestGitStash(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")

    @patch("subprocess.run")
    def test_get_git_stash_list(self, mock_run):
        mock_output = "stash@{0}: On main: WIP\nstash@{1}: On feature: Fix\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        stashes = get_git_stash_list(self.project_dir)
        self.assertEqual(len(stashes), 2)
        self.assertEqual(stashes[0]["index"], "0")
        self.assertEqual(stashes[0]["name"], "stash@{0}")
        self.assertEqual(stashes[0]["message"], "WIP")
        self.assertEqual(stashes[1]["index"], "1")

    @patch("subprocess.run")
    def test_get_stash_show(self, mock_run):
        mock_output = "diff content"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        diff = get_stash_show(self.project_dir, "stash@{0}")
        self.assertEqual(diff, "diff content")
        mock_run.assert_called_with(
            ["git", "stash", "show", "-p", "stash@{0}"],
            cwd=self.project_dir, capture_output=True, text=True, check=True
        )

    @patch("shared.git.run_git")
    def test_stash_push(self, mock_run_git):
        mock_run_git.return_value = True
        result = stash_push(self.project_dir, "my stash")
        self.assertTrue(result)
        mock_run_git.assert_called_with(["stash", "push", "-m", "my stash"], self.project_dir)

    @patch("shared.git.run_git")
    def test_stash_pop(self, mock_run_git):
        mock_run_git.return_value = True
        result = stash_pop(self.project_dir, "stash@{0}")
        self.assertTrue(result)
        mock_run_git.assert_called_with(["stash", "pop", "stash@{0}"], self.project_dir)

if __name__ == "__main__":
    unittest.main()
