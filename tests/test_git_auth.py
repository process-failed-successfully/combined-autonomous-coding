
import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.git import configure_git_auth  # noqa: E402


class TestGitAuth(unittest.TestCase):

    @patch("shared.git.subprocess.run")
    def test_configure_git_auth_github(self, mock_run):
        """Test default GitHub configuration."""
        configure_git_auth("mytoken")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        # Verify git config structure
        self.assertIn("git", args)
        self.assertIn("config", args)
        self.assertIn("--global", args)

        # Verify Rewrite Rule
        # https://x-access-token:mytoken@github.com/
        expected_key = "url.https://x-access-token:mytoken@github.com/.insteadOf"
        expected_value = "https://github.com/"

        self.assertIn(expected_key, args)
        self.assertIn(expected_value, args)

    @patch("shared.git.subprocess.run")
    def test_configure_git_auth_ghe(self, mock_run):
        """Test GHE configuration."""
        configure_git_auth("ghetoken", host="github.corp.com", username="myuser")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        # Verify Rewrite Rule
        # https://myuser:ghetoken@github.corp.com/
        expected_key = "url.https://myuser:ghetoken@github.corp.com/.insteadOf"
        expected_value = "https://github.corp.com/"

        self.assertIn(expected_key, args)
        self.assertIn(expected_value, args)

    @patch("shared.git.logger")
    @patch("shared.git.subprocess.run")
    def test_configure_git_auth_error_safety(self, mock_run, mock_logger):
        """Test that token is not leaked in logs when git command fails."""
        import subprocess

        token = "SECRET_TOKEN_123"
        # Simulate failure
        cmd = ["git", "config", "--global", f"url.https://x-access-token:{token}@github.com/.insteadOf", "https://github.com/"]

        # raise CalledProcessError
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=cmd,
            stderr=b"fatal: cannot lock config file"
        )
        mock_run.side_effect = error

        configure_git_auth(token)

        # Assert logger was called with error
        self.assertTrue(mock_logger.error.called)

        # Check all calls to logger.error for the token
        for call_args in mock_logger.error.call_args_list:
            log_msg = call_args[0][0] # First arg is the message
            self.assertNotIn(token, log_msg, "Token leaked in log message!")


if __name__ == "__main__":
    unittest.main()
