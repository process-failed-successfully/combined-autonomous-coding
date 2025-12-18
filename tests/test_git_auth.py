
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.git import configure_git_auth

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

if __name__ == "__main__":
    unittest.main()
