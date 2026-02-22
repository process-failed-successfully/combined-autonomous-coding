import unittest
from unittest.mock import patch, MagicMock
from shared.ollama_lab import OllamaLabManager

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
        import requests
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
        mock_post.assert_called()

    @patch('requests.delete')
    def test_delete_model(self, mock_delete):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        self.assertTrue(self.manager.delete_model("llama3"))

    @patch('requests.post')
    def test_chat(self, mock_post):
        # Mock streaming response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # iter_lines returns bytes
        mock_response.iter_lines.return_value = [
            b'{"message": {"content": "Hello"}, "done": false}',
            b'{"message": {"content": " World"}, "done": true}'
        ]
        # Context manager
        mock_post.return_value.__enter__.return_value = mock_response

        chunks = list(self.manager.chat("llama3", "Hi"))
        self.assertEqual("".join(chunks), "Hello World")

if __name__ == '__main__':
    unittest.main()
