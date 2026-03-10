import unittest
from unittest.mock import patch, MagicMock
from shared.http_lab import HttpLabManager

class TestHttpLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HttpLabManager()

    @patch('shared.http_lab.requests.request')
    def test_request_success(self, mock_request):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.url = "http://example.com"
        mock_response.ok = True
        mock_response.is_redirect = False
        mock_response.cookies.get_dict.return_value = {}
        mock_response.encoding = 'utf-8'

        mock_request.return_value = mock_response

        # Execute
        result = self.manager.request("GET", "http://example.com")

        # Verify
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['json'], {"message": "success"})
        self.assertEqual(result['ok'], True)
        mock_request.assert_called_once_with("GET", "http://example.com")

    @patch('shared.http_lab.requests.request')
    def test_request_error(self, mock_request):
        mock_request.side_effect = Exception("Connection refused")

        result = self.manager.request("GET", "http://example.com")

        self.assertIn("error", result)
        self.assertEqual(result['error'], "Connection refused")

    @patch('shared.http_lab.requests.request')
    def test_url_prefix(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Mock attributes accessed by HttpLabManager
        mock_response.reason = "OK"
        mock_response.headers = {}
        mock_response.text = ""
        mock_response.json.return_value = None
        mock_response.url = "http://example.com"
        mock_response.ok = True
        mock_response.is_redirect = False
        mock_response.cookies.get_dict.return_value = {}
        mock_response.encoding = 'utf-8'

        mock_request.return_value = mock_response

        self.manager.request("GET", "example.com") # Missing http://

        # Should add http://
        mock_request.assert_called_once_with("GET", "http://example.com")

    def test_parse_curl_basic_get(self):
        curl_cmd = "curl http://example.com"
        result = self.manager.parse_curl(curl_cmd)
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], "http://example.com")
        self.assertEqual(result['method'], "GET")
        self.assertEqual(result['headers'], {})
        self.assertIsNone(result['data'])

    def test_parse_curl_post_with_data(self):
        curl_cmd = "curl -X POST http://example.com -d '{\"key\": \"value\"}'"
        result = self.manager.parse_curl(curl_cmd)
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], "http://example.com")
        self.assertEqual(result['method'], "POST")
        self.assertEqual(result['data'], '{"key": "value"}')

    def test_parse_curl_with_headers_and_auth(self):
        curl_cmd = "curl -H 'Content-Type: application/json' -u user:pass http://example.com"
        result = self.manager.parse_curl(curl_cmd)
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], "http://example.com")
        self.assertEqual(result['method'], "GET")  # defaults to GET
        self.assertIn('Content-Type', result['headers'])
        self.assertEqual(result['headers']['Content-Type'], 'application/json')
        self.assertIn('Authorization', result['headers'])
        self.assertTrue(result['headers']['Authorization'].startswith('Basic '))

    def test_parse_curl_invalid(self):
        # Empty string
        self.assertIsNone(self.manager.parse_curl(""))
        # Unmatched quotes
        self.assertIsNone(self.manager.parse_curl("curl http://example.com -d '{\"key\""))

if __name__ == '__main__':
    unittest.main()
