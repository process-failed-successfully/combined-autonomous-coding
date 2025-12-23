import shared.git_wrapper as git_wrapper
import unittest
from unittest.mock import patch
import sys
from io import StringIO
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import module to test - we need to import it carefully as it's a script
# We can import it as a module


class TestGitWrapper(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_current_branch_success(self, mock_run):
        mock_run.return_value.stdout = "feature-branch\n"
        branch = git_wrapper.get_current_branch()
        self.assertEqual(branch, "feature-branch")

    @patch("subprocess.run")
    def test_get_current_branch_failure(self, mock_run):
        mock_run.side_effect = Exception("git error")
        branch = git_wrapper.get_current_branch()
        self.assertIsNone(branch)

    @patch("sys.argv", ["git", "status"])
    @patch("os.execvp")
    def test_main_passthrough(self, mock_execvp):
        # Should just pass through for non-push commands
        git_wrapper.main()
        mock_execvp.assert_called_with("git.real", ["git.real", "status"])

    @patch("sys.argv", ["git", "push", "origin", "main"])
    @patch("shared.git_wrapper.get_current_branch")
    def test_main_push_blocked_explicit(self, mock_get_branch):
        mock_get_branch.return_value = "feature"
        with self.assertRaises(SystemExit) as cm:
            # Capture stderr
            with patch('sys.stderr', new=StringIO()) as fake_err:
                git_wrapper.main()

        self.assertEqual(cm.exception.code, 1)

    @patch("sys.argv", ["git", "push"])
    @patch("shared.git_wrapper.get_current_branch")
    @patch("os.execvp")
    def test_main_push_allowed_implicit(self, mock_execvp, mock_get_branch):
        mock_get_branch.return_value = "feature-branch"
        git_wrapper.main()
        mock_execvp.assert_called_with("git.real", ["git.real", "push"])

    @patch("sys.argv", ["git", "push"])
    @patch("shared.git_wrapper.get_current_branch")
    def test_main_push_blocked_implicit_main(self, mock_get_branch):
        mock_get_branch.return_value = "main"
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=StringIO()) as fake_err:
                git_wrapper.main()
        self.assertEqual(cm.exception.code, 1)

    @patch("sys.argv", ["git", "push", "origin", "feature"])
    @patch("shared.git_wrapper.get_current_branch")
    @patch("os.execvp")
    def test_main_push_allowed_explicit_feature(self, mock_execvp, mock_get_branch):
        mock_get_branch.return_value = "main"  # On main, but pushing feature branch explicitly
        git_wrapper.main()
        mock_execvp.assert_called_with("git.real", ["git.real", "push", "origin", "feature"])

    @patch("sys.argv", ["git", "status"])
    @patch("os.execvp")
    def test_main_execvp_error_testing(self, mock_execvp):
        mock_execvp.side_effect = FileNotFoundError()
        with patch.dict("os.environ", {"GIT_WRAPPER_TESTING": "1"}):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stderr', new=StringIO()) as fake_err:
                    git_wrapper.main()
            self.assertEqual(cm.exception.code, 0)

    @patch("sys.argv", ["git", "status"])
    @patch("os.execvp")
    def test_main_execvp_error_no_testing(self, mock_execvp):
        mock_execvp.side_effect = FileNotFoundError()
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                with patch('sys.stderr', new=StringIO()) as fake_err:
                    git_wrapper.main()
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
