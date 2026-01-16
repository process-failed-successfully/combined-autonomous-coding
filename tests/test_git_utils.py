import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import sys

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.git_utils import is_safe_git_ref

class TestGitUtils(unittest.TestCase):

    @patch('subprocess.run')
    def test_is_safe_git_ref_valid_refs(self, mock_subprocess_run):
        """Test that valid git references are considered safe."""
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        valid_refs = [
            "main",
            "feature/new-branch",
            "v1.0.0",
            "HEAD",
            "HEAD~2",
            "a0c4d8e",
            "a0c4d8ef1b2a3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
            "refs/heads/main",
        ]
        for ref in valid_refs:
            with self.subTest(ref=ref):
                self.assertTrue(is_safe_git_ref(ref))
                mock_subprocess_run.assert_called_with(
                    ['git', 'check-ref-format', '--allow-onelevel', ref],
                    check=True, capture_output=True, text=True
                )

    @patch('subprocess.run')
    def test_is_safe_git_ref_invalid_refs(self, mock_subprocess_run):
        """Test that invalid git references are considered unsafe."""
        # Mock the subprocess to raise an error, simulating git's rejection
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "git")

        invalid_refs = [
            "feature/branch..with.dots",
            "branch-with-@",
            "branch-with-a-space",
            "\\branch-with-backslash",
        ]
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                self.assertFalse(is_safe_git_ref(ref))

    def test_is_safe_git_ref_leading_dash(self):
        """Test that references starting with a dash are unsafe."""
        self.assertFalse(is_safe_git_ref("-d"))
        self.assertFalse(is_safe_git_ref("--delete"))

    def test_is_safe_git_ref_empty_string(self):
        """Test that an empty string is unsafe."""
        self.assertFalse(is_safe_git_ref(""))

    @patch('subprocess.run', side_effect=FileNotFoundError)
    def test_is_safe_git_ref_git_not_found(self, mock_subprocess_run):
        """Test that the function returns False if git command is not found."""
        self.assertFalse(is_safe_git_ref("main"))

if __name__ == '__main__':
    unittest.main()
