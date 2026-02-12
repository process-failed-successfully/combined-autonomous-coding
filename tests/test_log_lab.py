import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.log_lab import LogLabManager
from shared.log_explorer import AgentStep, LogEntry

class TestLogLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = LogLabManager()

    @patch('shared.log_explorer.LogParser.parse_run')
    def test_parse_steps(self, mock_parse_run):
        mock_steps = [
            AgentStep(step_id=1, timestamp="10:00:00", description="Desc 1", details="Details 1", type="INFO"),
            AgentStep(step_id=2, timestamp="10:00:01", description="Desc 2", details="Details 2", type="ERROR")
        ]
        mock_parse_run.return_value = mock_steps

        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.parse(Path("test.log"), mode="steps")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[1]['type'], "ERROR")

    @patch('shared.log_explorer.LogParser._parse_entries')
    def test_parse_raw(self, mock_parse_entries):
        mock_entries = [
            LogEntry(timestamp="10:00:00", level="INFO", message="Message 1"),
            LogEntry(timestamp="10:00:01", level="ERROR", message="Message 2")
        ]
        mock_parse_entries.return_value = mock_entries

        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.parse(Path("test.log"), mode="raw")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['level'], "INFO")
        self.assertEqual(result[1]['message'], "Message 2")

    @patch('shared.log_explorer.LogParser._parse_entries')
    def test_filter_logs(self, mock_parse_entries):
        mock_entries = [
            LogEntry(timestamp="10:00:00", level="INFO", message="Starting process"),
            LogEntry(timestamp="10:00:01", level="DEBUG", message="Debugging"),
            LogEntry(timestamp="10:00:02", level="ERROR", message="Failed to connect"),
            LogEntry(timestamp="10:00:03", level="INFO", message="Process finished")
        ]
        mock_parse_entries.return_value = mock_entries

        # Filter by level
        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.filter_logs(Path("test.log"), level="ERROR")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['level'], "ERROR")

        # Filter by pattern
        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.filter_logs(Path("test.log"), pattern="Process")
        self.assertEqual(len(result), 2)

        # Filter by limit
        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.filter_logs(Path("test.log"), limit=1)
        self.assertEqual(len(result), 1)

    @patch('shared.log_explorer.LogParser._parse_entries')
    def test_stats(self, mock_parse_entries):
        mock_entries = [
            LogEntry(timestamp="10:00:00", level="INFO", message="Msg 1"),
            LogEntry(timestamp="10:00:01", level="ERROR", message="Error A"),
            LogEntry(timestamp="10:00:02", level="ERROR", message="Error A"),
            LogEntry(timestamp="10:00:03", level="INFO", message="Msg 2")
        ]
        mock_parse_entries.return_value = mock_entries

        with patch('pathlib.Path.exists', return_value=True):
            stats = self.manager.stats(Path("test.log"))

        self.assertEqual(stats['total_entries'], 4)
        self.assertEqual(stats['levels']['INFO'], 2)
        self.assertEqual(stats['levels']['ERROR'], 2)
        self.assertEqual(stats['error_count'], 2)
        self.assertEqual(stats['error_rate'], "50.00%")
        self.assertEqual(stats['top_messages'][0][0], "Error A")
        self.assertEqual(stats['top_messages'][0][1], 2)

if __name__ == '__main__':
    unittest.main()
