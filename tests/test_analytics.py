
import unittest
from typing import Any
from unittest.mock import patch
from pathlib import Path

from shared.analytics import (
    collect_analytics_data,
    get_git_contributors,
    get_git_hotspots,
    get_git_activity,
    _run_analytics_git_logic
)


class TestAnalytics(unittest.TestCase):

    @patch("shared.debt.scan_todos")
    @patch("shared.debt.analyze_project_complexity")
    @patch("shared.debt.find_duplicates")
    @patch("shared.debt.UnusedCodeDetector")
    @patch("shared.security.SecurityAuditor.scan_secrets")
    def test_collect_analytics_data(self, mock_scan_secrets: Any, mock_unused: Any, mock_duplication: Any, mock_complexity: Any, mock_todos: Any) -> None:  # pylint: disable=too-many-arguments
        """Test collecting overall analytics data."""
        # Mock Data for Debt
        mock_todos.return_value = [{"tag": "TODO", "text": "Fix"}]
        mock_complexity.return_value = [{"function": "f", "complexity": 5}]
        mock_duplication.return_value = []
        mock_unused.return_value.get_unused_definitions.return_value = []

        # Mock Data for Security
        mock_scan_secrets.return_value = [
            {"severity": "HIGH", "type": "secret", "file": "foo.py", "line": 1, "description": "AWS Key"}
        ]

        # Call the actual function
        data = collect_analytics_data(Path("."))

        # Assertions on structure
        self.assertIn("debt", data)
        self.assertIn("security", data)

        # Debt assertions
        self.assertEqual(data["debt"]["metrics"]["todos"]["count"], 1)
        # 1 todo = 1 point -> A
        self.assertEqual(data["debt"]["grade"], "A")

        # Security assertions
        self.assertEqual(len(data["security"]), 1)
        self.assertEqual(data["security"][0]["severity"], "HIGH")

    @patch('shared.analytics.shutil.which')
    @patch('shared.analytics.subprocess.run')
    def test_get_git_contributors(self, mock_run: Any, mock_which: Any) -> None:
        """Test getting git contributors."""
        mock_which.return_value = '/usr/bin/git'

        # Mock git shortlog output
        mock_run.return_value.stdout = "10\tAlice\n5\tBob\n2\tCharlie"
        mock_run.return_value.returncode = 0

        contributors = get_git_contributors(Path('.'))

        self.assertEqual(len(contributors), 3)
        self.assertEqual(contributors[0], (10, 'Alice'))
        self.assertEqual(contributors[1], (5, 'Bob'))
        self.assertEqual(contributors[2], (2, 'Charlie'))

    @patch('shared.analytics.shutil.which')
    @patch('shared.analytics.subprocess.run')
    def test_get_git_hotspots(self, mock_run: Any, mock_which: Any) -> None:
        """Test getting git hotspots."""
        mock_which.return_value = '/usr/bin/git'

        # Mock git log output (list of changed files)
        mock_run.return_value.stdout = "file1.py\nfile2.py\nfile1.py\nfile3.py\nfile1.py\nfile2.py"
        mock_run.return_value.returncode = 0

        hotspots = get_git_hotspots(Path('.'), limit=2)

        self.assertEqual(len(hotspots), 2)
        self.assertEqual(hotspots[0], ('file1.py', 3))
        self.assertEqual(hotspots[1], ('file2.py', 2))

    @patch('shared.analytics.shutil.which')
    @patch('shared.analytics.subprocess.run')
    def test_get_git_activity(self, mock_run: Any, mock_which: Any) -> None:
        """Test getting git activity."""
        mock_which.return_value = '/usr/bin/git'

        # Mock git log output (dates)
        mock_run.return_value.stdout = "2023-10-26\n2023-10-26\n2023-10-27\n2023-10-25"
        mock_run.return_value.returncode = 0

        activity = get_git_activity(Path('.'), days=30)

        self.assertEqual(len(activity), 3)
        # Should be sorted by date
        self.assertEqual(activity[0], ('2023-10-25', 1))
        self.assertEqual(activity[1], ('2023-10-26', 2))
        self.assertEqual(activity[2], ('2023-10-27', 1))

    @patch('shared.analytics.shutil.which')
    def test_analytics_no_git(self, mock_which: Any) -> None:
        """Test analytics when git is not available."""
        mock_which.return_value = None

        self.assertEqual(get_git_contributors(Path('.')), [])
        self.assertEqual(get_git_hotspots(Path('.')), [])
        self.assertEqual(get_git_activity(Path('.')), [])

    @patch('builtins.print')
    @patch('shared.analytics.get_git_activity')
    @patch('shared.analytics.get_git_hotspots')
    @patch('shared.analytics.get_git_contributors')
    @patch('pathlib.Path.is_dir')
    def test_run_analytics_git_logic(self, mock_is_dir: Any, mock_contributors: Any, mock_hotspots: Any, mock_activity: Any, mock_print: Any) -> None:
        """Test the orchestration function."""
        # 1. Test not a git repo
        mock_is_dir.return_value = False
        _run_analytics_git_logic(Path("."))
        mock_print.assert_any_call("❌ Error: Not a git repository.")

        # 2. Test git repo
        mock_is_dir.return_value = True
        mock_contributors.return_value = [(10, "Alice")]
        mock_hotspots.return_value = [("file.py", 5)]
        mock_activity.return_value = [("2023-01-01", 5)]

        _run_analytics_git_logic(Path("."))

        # Verify calls
        mock_contributors.assert_called()
        mock_hotspots.assert_called()
        mock_activity.assert_called()


if __name__ == '__main__':
    unittest.main()
