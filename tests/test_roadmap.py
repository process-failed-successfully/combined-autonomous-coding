import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from shared.roadmap import run_roadmap_logic
from shared.feature_list import save_feature_list

class TestRoadmap(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_path = self.test_dir / "feature_list.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.roadmap.Console")
    def test_roadmap_no_file(self, mock_console_cls):
        mock_console = mock_console_cls.return_value
        result = run_roadmap_logic(self.test_dir)
        self.assertFalse(result)
        mock_console.print.assert_called() # Should print error

    @patch("shared.roadmap.Console")
    def test_roadmap_empty(self, mock_console_cls):
        self.file_path.write_text("[]")
        mock_console = mock_console_cls.return_value
        result = run_roadmap_logic(self.test_dir)
        self.assertTrue(result)
        mock_console.print.assert_called() # Should print warning

    @patch("shared.roadmap.Console")
    def test_roadmap_success(self, mock_console_cls):
        data = [
            {"id": "1", "title": "F1", "passes": True},
            {"id": "2", "title": "F2", "status": "failed"},
            {"id": "3", "title": "F3", "status": "in_progress"},
            {"id": "4", "title": "F4"} # Pending
        ]
        save_feature_list(self.file_path, data)

        mock_console = mock_console_cls.return_value
        result = run_roadmap_logic(self.test_dir)
        self.assertTrue(result)

        # Verify calls. We expect multiple prints (header, progress, table)
        self.assertGreater(mock_console.print.call_count, 3)

if __name__ == "__main__":
    unittest.main()
