import unittest
from unittest.mock import patch, MagicMock
import argparse
from io import StringIO
from shared.http_lab import HttpLabManager, run_http_lab_logic

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

    def test_generate_curl_get(self):
        result = self.manager.generate_curl("GET", "http://example.com", headers={"Accept": "application/json"})
        self.assertEqual(result, 'curl -X GET "http://example.com" -H "Accept: application/json"')

    def test_generate_curl_post_data(self):
        result = self.manager.generate_curl("POST", "example.com", data="test=1")
        self.assertEqual(result, 'curl -X POST "http://example.com" -d \'test=1\'')

    def test_generate_curl_post_json(self):
        result = self.manager.generate_curl("POST", "http://api.example.com", json_data={"a": 1})
        self.assertEqual(result, 'curl -X POST "http://api.example.com" -H "Content-Type: application/json" -d \'{"a": 1}\'')

    def test_generate_curl_escape_quotes(self):
        # testing escaped quotes in headers and escaped quotes in json_data
        result = self.manager.generate_curl("POST", "http://api.example.com", headers={"X-Header": 'my"val'}, data="value='test'")
        self.assertEqual(result, 'curl -X POST "http://api.example.com" -H "X-Header: my\\"val" -d \'value=\'\\\'\'test\'\\\'\'\'')

class TestHttpLabLogic(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_to_curl(self, mock_stdout):
        args = argparse.Namespace(
            method="GET",
            url="http://example.com",
            header=["Accept: application/json"],
            data=None,
            json=None,
            proxy=None,
            to_curl=True,
            curl=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_http_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, 'curl -X GET "http://example.com" -H "Accept: application/json"')

    @patch('shared.http_lab.HttpLabManager.request')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_with_curl(self, mock_stdout, mock_request):
        mock_request.return_value = {
            "status_code": 200,
            "reason": "OK",
            "headers": {},
            "body": "success",
            "json": None,
            "elapsed": 0.1,
            "url": "http://example.com",
            "ok": True,
            "is_redirect": False,
            "cookies": {},
            "encoding": "utf-8"
        }
        args = argparse.Namespace(
            method="GET", # Should be overridden
            url="http://other.com", # Should be overridden
            header=None,
            data=None,
            json=None,
            proxy=None,
            to_curl=False,
            curl="curl -X POST http://example.com -H 'X-Test: 1' -d 'data'"
        )

        with self.assertRaises(SystemExit) as cm:
            run_http_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        mock_request.assert_called_once_with(
            "POST",
            "http://example.com",
            headers={"X-Test": "1"},
            timeout=10.0,
            allow_redirects=False,
            verify=True,
            data="data"
        )

if __name__ == '__main__':
    unittest.main()
