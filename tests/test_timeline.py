import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from datetime import datetime
from shared.timeline import TimelineCollector, TimelineRenderer, TimelineEvent

class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.collector = TimelineCollector(self.project_dir)

    @patch("shared.timeline.shutil.which")
    @patch("shared.timeline.subprocess.run")
    def test_collect_git_events(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/git"

        # Mock git log output
        # Format: ISO Date | Author | Message | Hash
        mock_output = "2023-10-26T12:00:00+00:00|Alice|Initial commit|abc1234\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        # Mock .git directory existence
        with patch.object(Path, "is_dir", return_value=True):
            events = self.collector.collect_git_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, "git")
        self.assertEqual(events[0].title, "Commit: Initial commit")
        self.assertEqual(events[0].timestamp.year, 2023)

    @patch("shared.timeline.Path.glob")
    @patch("shared.timeline.Path.exists")
    def test_collect_session_events(self, mock_exists, mock_glob):
        mock_exists.return_value = True

        # Mock session file
        mock_file = MagicMock()
        mock_file.read_text.return_value = '{"name": "test-session", "created_at": "2023-10-27T10:00:00"}'
        mock_file.name = "test-session.json"

        mock_glob.return_value = [mock_file]

        events = self.collector.collect_session_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, "session")
        self.assertEqual(events[0].title, "Session Created: test-session")

    def test_render_text(self):
        renderer = TimelineRenderer()
        events = [
            TimelineEvent(
                timestamp=datetime(2023, 10, 26, 12, 0),
                type="git",
                title="Commit: Init"
            )
        ]
        output = renderer.render_text(events)
        self.assertIn("Commit: Init", output)
        self.assertIn("GIT", output)

    def test_render_json(self):
        renderer = TimelineRenderer()
        events = [
            TimelineEvent(
                timestamp=datetime(2023, 10, 26, 12, 0),
                type="git",
                title="Commit: Init"
            )
        ]
        output = renderer.render_json(events)
        self.assertIn('"type": "git"', output)
        self.assertIn('"title": "Commit: Init"', output)

if __name__ == "__main__":
    unittest.main()
