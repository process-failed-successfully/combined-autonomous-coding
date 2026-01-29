import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.kata import KataManager

class TestKataManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = KataManager(self.project_dir)

    @patch("shared.kata.analyze_project_complexity")
    def test_list_challenges(self, mock_analyze):
        mock_analyze.return_value = [
            {"file": "a.py", "function": "complex_func", "complexity": 15, "lineno": 10},
            {"file": "b.py", "function": "simple_func", "complexity": 2, "lineno": 5},
            {"file": "c.py", "function": "med_func", "complexity": 8, "lineno": 20},
        ]

        # Test default threshold (5)
        challenges = self.manager.list_challenges()
        self.assertEqual(len(challenges), 2)
        self.assertEqual(challenges[0]["function"], "complex_func")
        self.assertEqual(challenges[1]["function"], "med_func")

        # Test limit
        challenges_limited = self.manager.list_challenges(limit=1)
        self.assertEqual(len(challenges_limited), 1)
        self.assertEqual(challenges_limited[0]["function"], "complex_func")

    @patch("shared.kata.process_file")
    def test_verify_improvement_success(self, mock_process):
        # Mocking the file processing result
        mock_process.return_value = [
            {"file": "a.py", "function": "target_func", "complexity": 5, "lineno": 10}
        ]

        # Check if file exists (mocking Path.exists)
        with patch.object(Path, "exists", return_value=True):
            # Original was 15, new is 5
            result = self.manager.verify_improvement("a.py", "target_func", 15)

            self.assertTrue(result["success"])
            self.assertIn("reduced from 15 to 5", result["message"])

    @patch("shared.kata.process_file")
    def test_verify_improvement_failure(self, mock_process):
        mock_process.return_value = [
            {"file": "a.py", "function": "target_func", "complexity": 15, "lineno": 10}
        ]

        with patch.object(Path, "exists", return_value=True):
            # Original was 15, new is 15 (no change)
            result = self.manager.verify_improvement("a.py", "target_func", 15)

            self.assertFalse(result["success"])
            self.assertIn("still 15", result["message"])

    @patch("shared.kata.process_file")
    def test_verify_improvement_worse(self, mock_process):
        mock_process.return_value = [
            {"file": "a.py", "function": "target_func", "complexity": 20, "lineno": 10}
        ]

        with patch.object(Path, "exists", return_value=True):
            # Original was 15, new is 20 (worse)
            result = self.manager.verify_improvement("a.py", "target_func", 15)

            self.assertFalse(result["success"])
            self.assertIn("increased to 20", result["message"])

    @patch("shared.kata.process_file")
    def test_verify_improvement_not_found(self, mock_process):
        mock_process.return_value = [] # Function gone?

        with patch.object(Path, "exists", return_value=True):
            result = self.manager.verify_improvement("a.py", "missing_func", 15)

            self.assertFalse(result["success"])
            self.assertIn("not found", result["message"])

if __name__ == "__main__":
    unittest.main()
