import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.branch_lab import BranchLabManager
import subprocess


class TestBranchLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/mock_project")
        self.manager = BranchLabManager(self.project_dir)

    @patch("shared.branch_lab.subprocess.run")
    def test_get_main_branch(self, mock_run):
        # Mock successful rev-parse for 'main'
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        self.assertEqual(self.manager._get_main_branch(), "main")
        mock_run.assert_called_with(["git", "-C", str(self.project_dir), "rev-parse", "--verify", "main"], capture_output=True, text=True, check=True)

        # Mock 'main' fails, 'master' succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            MagicMock(stdout="", returncode=0)
        ]
        self.assertEqual(self.manager._get_main_branch(), "master")

    @patch("shared.branch_lab.BranchLabManager._get_main_branch")
    @patch("shared.branch_lab.subprocess.run")
    def test_get_all_branches(self, mock_run, mock_get_main):
        mock_get_main.return_value = "main"

        # Mock the merged branches call
        merged_output = "  feature-a\n* main\n  bugfix-1\n"

        # Mock the for-each-ref call
        # Format: refname:short|authorname|committerdate:short|subject|refname
        ref_output = (
            "main|Alice|2023-01-01|Initial|refs/heads/main\n"
            "feature-a|Bob|2023-01-02|Add a|refs/heads/feature-a\n"
            "feature-b|Charlie|2023-01-03|Add b|refs/heads/feature-b\n"
            "origin/main|Alice|2023-01-01|Initial|refs/remotes/origin/main\n"
            "origin/feature-a|Bob|2023-01-02|Add a|refs/remotes/origin/feature-a\n"
        )

        mock_run.side_effect = [
            MagicMock(stdout=merged_output, returncode=0),
            MagicMock(stdout=ref_output, returncode=0)
        ]

        branches = self.manager.get_all_branches()
        self.assertEqual(len(branches), 5)

        # Verify main
        main_branch = next(b for b in branches if b["name"] == "main")
        self.assertEqual(main_branch["type"], "Local")
        self.assertEqual(main_branch["merged"], "Yes")  # main is always merged into itself

        # Verify feature-a (merged)
        feat_a = next(b for b in branches if b["name"] == "feature-a")
        self.assertEqual(feat_a["type"], "Local")
        self.assertEqual(feat_a["merged"], "Yes")
        self.assertEqual(feat_a["author"], "Bob")

        # Verify feature-b (not merged)
        feat_b = next(b for b in branches if b["name"] == "feature-b")
        self.assertEqual(feat_b["type"], "Local")
        self.assertEqual(feat_b["merged"], "No")

        # Verify remote origin/feature-a (merged because feature-a is merged)
        rem_feat_a = next(b for b in branches if b["name"] == "origin/feature-a")
        self.assertEqual(rem_feat_a["type"], "Remote")
        self.assertEqual(rem_feat_a["merged"], "Yes")

    @patch("shared.branch_lab.subprocess.run")
    def test_checkout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.manager.checkout("feature-a"))
        mock_run.assert_called_with(["git", "-C", str(self.project_dir), "checkout", "feature-a"], capture_output=True, text=True, check=True)

        mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="error")
        self.assertFalse(self.manager.checkout("bad-branch"))

    @patch("shared.branch_lab.subprocess.run")
    def test_delete_branches_local(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        results = self.manager.delete_branches(["feature-a", "feature-b"])

        self.assertEqual(results, {"feature-a": True, "feature-b": True})
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(["git", "-C", str(self.project_dir), "branch", "-d", "feature-a"], capture_output=True, text=True, check=True)
        mock_run.assert_any_call(["git", "-C", str(self.project_dir), "branch", "-d", "feature-b"], capture_output=True, text=True, check=True)

    @patch("shared.branch_lab.subprocess.run")
    def test_delete_branches_force(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        results = self.manager.delete_branches(["feature-a"], force=True)

        self.assertEqual(results, {"feature-a": True})
        mock_run.assert_called_with(["git", "-C", str(self.project_dir), "branch", "-D", "feature-a"], capture_output=True, text=True, check=True)

    @patch("shared.branch_lab.subprocess.run")
    def test_delete_branches_remote(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        results = self.manager.delete_branches(["origin/feature-a"])

        self.assertEqual(results, {"origin/feature-a": True})
        mock_run.assert_called_with(["git", "-C", str(self.project_dir), "push", "origin", "--delete", "feature-a"], capture_output=True, text=True, check=True)

    @patch("shared.branch_lab.subprocess.run")
    def test_delete_branches_failure(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),
            subprocess.CalledProcessError(1, "git", stderr="unmerged")
        ]

        results = self.manager.delete_branches(["feature-a", "feature-b"])

        self.assertEqual(results, {"feature-a": True, "feature-b": False})


if __name__ == "__main__":
    unittest.main()
