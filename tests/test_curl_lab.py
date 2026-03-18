import unittest
from unittest.mock import patch, MagicMock
import io
from shared.curl_lab import CurlLabManager, run_curl_lab_logic


class TestCurlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CurlLabManager()

    def test_parse_curl_basic_get(self):
        cmd = "curl https://api.example.com/data"
        parsed = self.manager.parse_curl(cmd)

        self.assertEqual(parsed['url'], "https://api.example.com/data")
        self.assertEqual(parsed['method'], "GET")
        self.assertEqual(parsed['headers'], {})
        self.assertIsNone(parsed['data'])
        self.assertIsNone(parsed['auth'])

    def test_parse_curl_post_json(self):
        cmd = "curl -X POST -H \"Content-Type: application/json\" -d '{\"key\":\"value\"}' https://api.example.com/data"
        parsed = self.manager.parse_curl(cmd)

        self.assertEqual(parsed['url'], "https://api.example.com/data")
        self.assertEqual(parsed['method'], "POST")
        self.assertEqual(parsed['headers'], {"Content-Type": "application/json"})
        self.assertEqual(parsed['data'], '{"key":"value"}')
        self.assertIsNone(parsed['auth'])

    def test_parse_curl_with_auth_and_user_agent(self):
        cmd = "curl -u admin:secret123 -A \"CustomAgent/1.0\" https://api.example.com"
        parsed = self.manager.parse_curl(cmd)

        self.assertEqual(parsed['url'], "https://api.example.com")
        self.assertEqual(parsed['method'], "GET")
        self.assertEqual(parsed['headers'], {"User-Agent": "CustomAgent/1.0"})
        self.assertEqual(parsed['auth'], ("admin", "secret123"))

    def test_parse_curl_head_request(self):
        cmd = "curl -I https://api.example.com"
        parsed = self.manager.parse_curl(cmd)

        self.assertEqual(parsed['method'], "HEAD")

    def test_parse_curl_cookie(self):
        cmd = "curl -b \"sessionid=123; user=alice\" https://api.example.com"
        parsed = self.manager.parse_curl(cmd)

        self.assertEqual(parsed['headers']['Cookie'], "sessionid=123; user=alice")

    def test_parse_invalid_curl(self):
        with self.assertRaises(ValueError):
            self.manager.parse_curl("wget https://api.example.com")

        with self.assertRaises(ValueError):
            self.manager.parse_curl("curl -X GET")  # Missing URL

    def test_to_python_requests_basic(self):
        parsed = {
            'url': 'https://api.example.com',
            'method': 'GET',
            'headers': {},
            'data': None,
            'auth': None
        }

        code = self.manager.to_python_requests(parsed)
        self.assertIn("import requests", code)
        self.assertIn("requests.get(url)", code)

    def test_to_python_requests_json_post(self):
        parsed = {
            'url': 'https://api.example.com',
            'method': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'data': '{"key": true}',
            'auth': None
        }

        code = self.manager.to_python_requests(parsed)
        self.assertIn("import json", code)
        self.assertIn("json_data = json.loads(", code)
        self.assertIn("requests.post(url, headers=headers, json=json_data)", code)

    def test_to_js_fetch_basic(self):
        parsed = {
            'url': 'https://api.example.com',
            'method': 'GET',
            'headers': {},
            'data': None,
            'auth': None
        }

        code = self.manager.to_js_fetch(parsed)
        self.assertIn("fetch('https://api.example.com'", code)
        self.assertIn("method: 'GET'", code)

    def test_to_js_fetch_with_auth(self):
        parsed = {
            'url': 'https://api.example.com',
            'method': 'GET',
            'headers': {},
            'data': None,
            'auth': ('user', 'pass')
        }

        code = self.manager.to_js_fetch(parsed)
        # base64 for 'user:pass' is 'dXNlcjpwYXNz'
        self.assertIn("'Authorization': 'Basic dXNlcjpwYXNz'", code)

    def test_to_go_http_post(self):
        parsed = {
            'url': 'https://api.example.com',
            'method': 'POST',
            'headers': {'Content-Type': 'text/plain'},
            'data': 'hello "world"',
            'auth': None
        }

        code = self.manager.to_go_http(parsed)
        self.assertIn('payload := strings.NewReader("hello \\"world\\"")', code)
        self.assertIn('http.NewRequest("POST", "https://api.example.com", payload)', code)

    def test_parse_curl_argparse_error(self):
        # argparse error like an unknown flag will be ignored by parse_known_args
        # But if the user provides an invalid option like --help or -h it would exit.
        # Check that it doesn't sys.exit
        with self.assertRaises(ValueError):
            self.manager.parse_curl("curl -h")


class TestCurlLabCli(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_python(self, mock_stdout):
        args = MagicMock()
        args.tui = False
        args.command_str = "curl https://api.example.com"
        args.target = "python"

        run_curl_lab_logic(args)
        output = mock_stdout.getvalue()

        self.assertIn("import requests", output)
        self.assertIn("requests.get", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_js(self, mock_stdout):
        args = MagicMock()
        args.tui = False
        args.command_str = "curl https://api.example.com"
        args.target = "js"

        run_curl_lab_logic(args)
        output = mock_stdout.getvalue()

        self.assertIn("fetch(", output)


if __name__ == '__main__':
    unittest.main()
