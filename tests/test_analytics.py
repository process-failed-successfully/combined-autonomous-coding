
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.analytics import get_git_contributors, get_git_hotspots, get_git_activity

class TestAnalytics(unittest.TestCase):

    @patch('shared.analytics.shutil.which')
    @patch('shared.analytics.subprocess.run')
    def test_get_git_contributors(self, mock_run, mock_which):
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
    def test_get_git_hotspots(self, mock_run, mock_which):
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
    def test_get_git_activity(self, mock_run, mock_which):
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
    def test_analytics_no_git(self, mock_which):
        """Test analytics when git is not available."""
        mock_which.return_value = None

        self.assertEqual(get_git_contributors(Path('.')), [])
        self.assertEqual(get_git_hotspots(Path('.')), [])
        self.assertEqual(get_git_activity(Path('.')), [])

if __name__ == '__main__':
    unittest.main()
