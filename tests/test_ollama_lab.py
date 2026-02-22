import unittest
from unittest.mock import patch, MagicMock
from shared.ollama_lab import OllamaLabManager
import requests

class TestOllamaLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = OllamaLabManager()

    @patch('requests.get')
    def test_check_connection_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.assertTrue(self.manager.check_connection())
        mock_get.assert_called_with(f"{self.manager.base_url}/api/tags", timeout=2)

    @patch('requests.get')
    def test_check_connection_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection refused")
        self.assertFalse(self.manager.check_connection())

    @patch('requests.get')
    def test_list_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "size": 1000},
                {"name": "mistral", "size": 2000}
            ]
        }
        mock_get.return_value = mock_response

        models = self.manager.list_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]['name'], "llama3")

    @patch('requests.post')
    def test_show_model_info(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"modelfile": "FROM llama3"}
        mock_post.return_value = mock_response

        info = self.manager.show_model_info("llama3")
        self.assertEqual(info['modelfile'], "FROM llama3")
        mock_post.assert_called_with(
            f"{self.manager.base_url}/api/show",
            json={"name": "llama3"},
            timeout=5
        )

    @patch('requests.delete')
    def test_delete_model(self, mock_delete):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        self.assertTrue(self.manager.delete_model("llama3"))
        mock_delete.assert_called_with(
            f"{self.manager.base_url}/api/delete",
            json={"name": "llama3"},
            timeout=10
        )

    @patch('requests.post')
    def test_pull_model(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"status": "pulling manifest"}',
            b'{"status": "downloading", "completed": 10, "total": 100}'
        ]
        # Context manager
        mock_post.return_value.__enter__.return_value = mock_response

        updates = list(self.manager.pull_model("llama3"))
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0]['status'], "pulling manifest")

        mock_post.assert_called_with(
            f"{self.manager.base_url}/api/pull",
            json={"name": "llama3"},
            stream=True,
            timeout=(10, 300)
        )

    @patch('requests.post')
    def test_chat(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"message": {"content": "Hello"}, "done": false}',
            b'{"message": {"content": " World"}, "done": true}'
        ]
        mock_post.return_value.__enter__.return_value = mock_response

        chunks = list(self.manager.chat("llama3", "Hi"))
        self.assertEqual("".join(chunks), "Hello World")

        # Verify call arguments including timeout
        mock_post.assert_called_with(
            f"{self.manager.base_url}/api/chat",
            json={"model": "llama3", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
            stream=True,
            timeout=(10, 120)
        )

if __name__ == '__main__':
    unittest.main()
