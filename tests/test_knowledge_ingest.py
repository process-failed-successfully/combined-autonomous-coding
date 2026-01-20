import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.knowledge import KnowledgeManager
from shared.database import init_db

class TestKnowledgeIngest(unittest.TestCase):

    def setUp(self):
        init_db(Path(":memory:"))
        self.manager = KnowledgeManager()

    def test_ingest_file(self):
        # Create a temp file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("This is a test file content.")
            temp_path = f.name

        try:
            item = self.manager.ingest_knowledge(temp_path, category="FILE_TEST")
            self.assertEqual(item.content, "This is a test file content.")
            self.assertEqual(item.category, "FILE_TEST")
            self.assertEqual(item.source_agent, f"file:{Path(temp_path).name}")
        finally:
            os.remove(temp_path)

    @patch('shared.knowledge.requests.get')
    def test_ingest_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>This is a test URL content.</p></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        url = "http://example.com/test"
        item = self.manager.ingest_knowledge(url, category="URL_TEST")

        self.assertEqual(item.content, "This is a test URL content.")
        self.assertEqual(item.category, "URL_TEST")
        self.assertEqual(item.source_agent, f"url:{url}")
        mock_get.assert_called_with(url, timeout=10)

    def test_ingest_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.ingest_knowledge("non_existent_file.txt")

    @patch('shared.knowledge.requests.get')
    def test_ingest_url_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with self.assertRaises(ValueError):
            self.manager.ingest_knowledge("http://example.com/error")

if __name__ == '__main__':
    unittest.main()
