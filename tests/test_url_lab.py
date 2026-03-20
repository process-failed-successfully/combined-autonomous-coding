import unittest
from unittest.mock import MagicMock, patch
from shared.url_lab import UrlLabManager, run_url_lab_logic
import json
import sys
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


if __name__ == '__main__':
    unittest.main()
