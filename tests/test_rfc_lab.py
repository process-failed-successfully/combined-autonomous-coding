import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from shared.rfc_lab import RFCLabManager

class TestRFCLabManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = RFCLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('requests.get')
    def test_update_index(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "0001 Test RFC. A. Author. April 1969.\n0002 Another RFC."
        mock_get.return_value = mock_response

        success = self.manager.update_index()
        self.assertTrue(success)
        self.assertTrue(self.manager.index_path.exists())
        self.assertEqual(self.manager.index_path.read_text(encoding='utf-8'), mock_response.text)

    @patch('requests.get')
    def test_search(self, mock_get):
        # Mock index update first
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "0001 Test RFC. A. Author. April 1969.\n0002 Another RFC."
        mock_get.return_value = mock_response

        self.manager.update_index()

        results = self.manager.search("Test RFC")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["number"], "0001")
        self.assertIn("Test RFC", results[0]["title"])

        results_empty = self.manager.search("Nonexistent")
        self.assertEqual(len(results_empty), 0)

    @patch('requests.get')
    def test_get_rfc(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "RFC Content"
        mock_get.return_value = mock_response

        content = self.manager.get_rfc("1")
        self.assertEqual(content, "RFC Content")

        # Check caching
        cache_file = self.manager.cache_dir / "rfc1.txt"
        self.assertTrue(cache_file.exists())
        self.assertEqual(cache_file.read_text(encoding='utf-8'), "RFC Content")

        # Test subsequent call uses cache (mock shouldn't be called if we didn't force,
        # but here we are calling function that checks cache first)
        mock_get.reset_mock()
        content_cached = self.manager.get_rfc("1")
        self.assertEqual(content_cached, "RFC Content")
        mock_get.assert_not_called()

if __name__ == '__main__':
    unittest.main()
