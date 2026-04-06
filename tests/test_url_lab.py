import unittest
from unittest.mock import MagicMock, patch
from shared.url_lab import UrlLabManager, run_url_lab_logic
import json
import io


class TestUrlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = UrlLabManager()

    def test_parse(self):
        url = "https://user:pass@example.com:8080/path/to/resource?query=param&key=val#fragment"
        result = self.manager.parse(url)
        self.assertEqual(result["scheme"], "https")
        self.assertEqual(result["netloc"], "user:pass@example.com:8080")
        self.assertEqual(result["path"], "/path/to/resource")
        self.assertEqual(result["query"], "query=param&key=val")
        self.assertEqual(result["fragment"], "fragment")
        self.assertEqual(result["query_params"], {"query": ["param"], "key": ["val"]})

    def test_extract(self):
        url = "https://user:pass@example.com:8080/path/to/resource?query=param&key=val#fragment"
        self.assertEqual(self.manager.extract(url, "scheme"), "https")
        self.assertEqual(self.manager.extract(url, "netloc"), "user:pass@example.com:8080")
        self.assertEqual(self.manager.extract(url, "hostname"), "example.com")
        self.assertEqual(self.manager.extract(url, "port"), "8080")
        self.assertEqual(self.manager.extract(url, "path"), "/path/to/resource")
        self.assertEqual(self.manager.extract(url, "query"), "query=param&key=val")
        self.assertEqual(self.manager.extract(url, "fragment"), "fragment")

        url_no_port = "https://example.com"
        self.assertEqual(self.manager.extract(url_no_port, "port"), "")
        self.assertEqual(self.manager.extract(url_no_port, "hostname"), "example.com")

        url_no_hostname = "file:///path/to/file"
        self.assertEqual(self.manager.extract(url_no_hostname, "hostname"), "")

        with self.assertRaises(ValueError):
            self.manager.extract(url, "invalid")

        url_invalid_port = "http://example.com:invalid/"
        self.assertEqual(self.manager.extract(url_invalid_port, "port"), "")

    def test_encode(self):
        text = "hello world/&?"
        encoded = self.manager.encode(text)
        self.assertEqual(encoded, "hello%20world/%26%3F")

    def test_decode(self):
        text = "hello%20world%2F%26%3F"
        decoded = self.manager.decode(text)
        self.assertEqual(decoded, "hello world/&?")

    def test_encode_plus(self):
        text = "hello world/&?"
        encoded = self.manager.encode_plus(text)
        self.assertEqual(encoded, "hello+world%2F%26%3F")

    def test_decode_plus(self):
        text = "hello+world%2F%26%3F"
        decoded = self.manager.decode_plus(text)
        self.assertEqual(decoded, "hello world/&?")

    def test_join(self):
        base = "http://example.com/api/"
        paths = ["v1", "users", "123"]
        # Note: urljoin behavior
        # 1. join(base, v1) -> http://example.com/api/v1
        # 2. join(prev, users) -> http://example.com/api/users (replaces v1 because no trailing slash)
        # 3. join(prev, 123) -> http://example.com/api/123
        result = self.manager.join(base, paths)
        self.assertEqual(result, "http://example.com/api/123")

        # Test with proper trailing slashes for appending
        base2 = "http://example.com/"
        paths2 = ["api/", "v1/", "users"]
        result2 = self.manager.join(base2, paths2)
        self.assertEqual(result2, "http://example.com/api/v1/users")

    def test_params_list(self):
        url = "http://example.com?foo=bar&baz=qux"
        result = self.manager.params(url, "list")
        data = json.loads(result)
        self.assertEqual(data["foo"], ["bar"])
        self.assertEqual(data["baz"], ["qux"])

    def test_params_get(self):
        url = "http://example.com?foo=bar&foo=baz"
        result = self.manager.params(url, "get", key="foo")
        data = json.loads(result)
        self.assertEqual(data, ["bar", "baz"])

    def test_params_add(self):
        url = "http://example.com?foo=bar"
        result = self.manager.params(url, "add", key="foo", value="baz")
        self.assertIn("foo=bar", result)
        self.assertIn("foo=baz", result)

    def test_params_set(self):
        url = "http://example.com?foo=bar&foo=baz"
        result = self.manager.params(url, "set", key="foo", value="new")
        self.assertIn("foo=new", result)
        self.assertNotIn("foo=bar", result)

    def test_params_remove(self):
        url = "http://example.com?foo=bar&baz=qux"
        result = self.manager.params(url, "remove", key="foo")
        self.assertNotIn("foo", result)
        self.assertIn("baz=qux", result)

    def test_normalize(self):
        url = "HTTP://Example.COM:80/foo?b=2&a=1"
        result = self.manager.normalize(url)
        self.assertEqual(result, "http://example.com/foo?a=1&b=2")

        url_https = "HTTPS://Example.COM:443/foo"
        result_https = self.manager.normalize(url_https)
        self.assertEqual(result_https, "https://example.com/foo")


class TestRunUrlLabLogic(unittest.TestCase):
    @patch('sys.exit', side_effect=SystemExit(0))
    def test_run_tui(self, mock_exit):
        """Test that action='tui' launches the URL Lab TUI."""
        from pathlib import Path
        args = MagicMock()
        args.action = "tui"
        args.project_dir = Path("mock_dir")

        # Mock async run
        async def mock_run_async(*args, **kwargs):
            pass

        # We need to mock AgentTUI before it gets imported and run by main
        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=MagicMock())}):
            import sys
            MockAgentTUI = sys.modules['shared.tui'].AgentTUI
            MockAgentTUI.return_value.run_async = mock_run_async
            from main import run_url_lab
            with self.assertRaises(SystemExit) as cm:
                run_url_lab(args)
            self.assertEqual(cm.exception.code, 0)
            MockAgentTUI.assert_called_with(project_dir=args.project_dir, start_tab="tab-url-lab")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_extract(self, mock_stdout):
        args = MagicMock()
        args.action = "extract"
        args.url = "http://example.com/path"
        args.component = "scheme"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "http")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_extract_error(self, mock_stderr):
        args = MagicMock()
        args.action = "extract"
        args.url = "http://example.com/path"
        args.component = "invalid"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Unknown component: invalid", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_parse(self, mock_stdout):
        args = MagicMock()
        args.action = "parse"
        args.url = "http://example.com"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn('"netloc": "example.com"', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_encode(self, mock_stdout):
        args = MagicMock()
        args.action = "encode"
        args.text = "hello world"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello%20world")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_encode_plus(self, mock_stdout):
        args = MagicMock()
        args.action = "encode-plus"
        args.text = "hello world"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello+world")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_decode(self, mock_stdout):
        args = MagicMock()
        args.action = "decode"
        args.text = "hello%20world"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello world")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_decode_plus(self, mock_stdout):
        args = MagicMock()
        args.action = "decode-plus"
        args.text = "hello+world"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello world")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_join(self, mock_stdout):
        args = MagicMock()
        args.action = "join"
        args.base = "http://example.com/api/"
        args.paths = ["v1", "users"]

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "http://example.com/api/users")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_params(self, mock_stdout):
        args = MagicMock()
        args.action = "params"
        args.url = "http://example.com?foo=bar"
        args.mode = "list"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn('"foo"', output)
        self.assertIn('"bar"', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_params_error(self, mock_stdout):
        args = MagicMock()
        args.action = "params"
        args.url = "http://example.com?foo=bar"
        args.mode = "get"
        # Ensure key is completely missing
        del args.key

        # Patch sys.stderr instead of stdout since we want to check the error message
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                run_url_lab_logic(args)

            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Error: Key required for 'get' mode", mock_stderr.getvalue())

    def test_params_add_error(self):
        manager = UrlLabManager()
        with self.assertRaises(ValueError):
            manager.params("http://example.com", "add", key="foo")  # missing value

    def test_params_set_error(self):
        manager = UrlLabManager()
        with self.assertRaises(ValueError):
            manager.params("http://example.com", "set", key="foo")  # missing value

    def test_params_remove_error(self):
        manager = UrlLabManager()
        with self.assertRaises(ValueError):
            manager.params("http://example.com", "remove")  # missing key

    def test_params_get_error(self):
        manager = UrlLabManager()
        with self.assertRaises(ValueError):
            manager.params("http://example.com", "get")  # missing key

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_normalize(self, mock_stdout):
        args = MagicMock()
        args.action = "normalize"
        args.url = "HTTP://Example.COM:80/foo"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "http://example.com/foo")

    @patch('shared.url_lab.requests.head')
    def test_unshorten(self, mock_head):
        # Setup mock for a successful redirect
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://final.com"
        mock_response.reason = "OK"

        mock_history = MagicMock()
        mock_history.url = "http://short.url"
        mock_history.status_code = 301
        mock_history.reason = "Moved Permanently"

        mock_response.history = [mock_history]
        mock_head.return_value = mock_response

        manager = UrlLabManager()
        result = manager.unshorten("http://short.url")

        self.assertEqual(result["initial_url"], "http://short.url")
        self.assertEqual(result["final_url"], "http://final.com")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["redirects"], 1)
        self.assertEqual(len(result["trace"]), 2)
        self.assertEqual(result["trace"][0]["url"], "http://short.url")
        self.assertEqual(result["trace"][1]["url"], "http://final.com")

    @patch('shared.url_lab.requests.head')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_unshorten(self, mock_stdout, mock_head):
        # Setup mock for a successful redirect
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://final.com"
        mock_response.reason = "OK"
        mock_response.history = []
        mock_head.return_value = mock_response

        args = MagicMock()
        args.action = "unshorten"
        args.url = "http://short.url"

        with self.assertRaises(SystemExit) as cm:
            run_url_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn('"initial_url": "http://short.url"', output)
        self.assertIn('"final_url": "http://final.com"', output)
