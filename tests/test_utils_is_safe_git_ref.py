import unittest
from shared.utils import is_safe_git_ref

class TestIsSafeGitRef(unittest.TestCase):
    def test_valid_refs(self):
        """Test valid git references."""
        valid_refs = [
            "master",
            "main",
            "feature/branch",
            "v1.0.0",
            "HEAD",
            "HEAD^",
            "HEAD~1",
            "HEAD@{1}",
            "user/repo/branch",
            "fix-bug",
            "underscore_name",
            "1234567",
            "a" * 40,  # long hash
        ]
        for ref in valid_refs:
            with self.subTest(ref=ref):
                self.assertTrue(is_safe_git_ref(ref), f"Should be valid: {ref}")

    def test_invalid_refs(self):
        """Test invalid git references that should be rejected."""
        invalid_refs = [
            "-flag", # Starts with dash
            "--option",
            "branch; rm -rf /", # Command injection
            "branch | ls",
            "branch && echo h",
            "branch`whoami`",
            "branch$(whoami)",
            "branch>output",
            "branch<input",
            " ", # Space not allowed
            "branch with space",
            "", # Empty string
            None, # None
        ]
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                self.assertFalse(is_safe_git_ref(ref), f"Should be invalid: {ref}")

if __name__ == "__main__":
    unittest.main()
