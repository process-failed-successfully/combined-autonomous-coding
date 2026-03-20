import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, RichLog, DataTable, Select
# Import the class under test
from shared.tui_url import UrlLabTab


class TestUrlLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch UrlLabManager at the source where it is imported in tui_url
        self.patcher = patch("shared.tui_url.UrlLabManager")
        self.MockManager = self.patcher.start()

        # Instantiate the tab
        self.tab = UrlLabTab()
        self.mock_manager = self.MockManager.return_value
        # Ensure the tab uses our mock instance
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_action_parse_success(self):
        # Mock Inputs
        url_input = MagicMock(spec=Input)
        url_input.value = "https://example.com"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-parse-input":
                return url_input
            if selector == "#url-parse-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.parse.return_value = {"scheme": "https", "netloc": "example.com"}

        # Run
        self.tab.action_parse()

        # Verify
        self.mock_manager.parse.assert_called_with("https://example.com")
        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("scheme", args[0])

    async def test_action_encode(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "hello world"
        select_widget = MagicMock(spec=Select)
        select_widget.value = "Standard (%20)"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-enc-input":
                return input_widget
            if selector == "#url-enc-mode":
                return select_widget
            if selector == "#url-enc-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.encode.return_value = "hello%20world"

        # Run
        self.tab.action_encode()

        # Verify
        self.mock_manager.encode.assert_called_with("hello world")
        log.write.assert_called_with("hello%20world")

    async def test_action_decode(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "hello%20world"
        select_widget = MagicMock(spec=Select)
        select_widget.value = "Standard (%20)"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-enc-input":
                return input_widget
            if selector == "#url-enc-mode":
                return select_widget
            if selector == "#url-enc-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.decode.return_value = "hello world"

        # Run
        self.tab.action_decode()

        # Verify
        self.mock_manager.decode.assert_called_with("hello%20world")
        log.write.assert_called_with("hello world")


    async def test_action_encode_plus(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "hello world"
        select_widget = MagicMock(spec=Select)
        select_widget.value = "Plus (+)"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-enc-input":
                return input_widget
            if selector == "#url-enc-mode":
                return select_widget
            if selector == "#url-enc-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.encode_plus.return_value = "hello+world"

        # Run
        self.tab.action_encode()

        # Verify
        self.mock_manager.encode_plus.assert_called_with("hello world")
        log.write.assert_called_with("hello+world")

    async def test_action_decode_plus(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "hello+world"
        select_widget = MagicMock(spec=Select)
        select_widget.value = "Plus (+)"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-enc-input":
                return input_widget
            if selector == "#url-enc-mode":
                return select_widget
            if selector == "#url-enc-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.decode_plus.return_value = "hello world"

        # Run
        self.tab.action_decode()

        # Verify
        self.mock_manager.decode_plus.assert_called_with("hello+world")
        log.write.assert_called_with("hello world")

    async def test_action_param_add(self):
        # Mock Inputs
        url_input = MagicMock(spec=Input)
        url_input.value = "http://example.com"
        key_input = MagicMock(spec=Input)
        key_input.value = "foo"
        val_input = MagicMock(spec=Input)
        val_input.value = "bar"
        log = MagicMock(spec=RichLog)
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#url-params-base":
                return url_input
            if selector == "#url-param-key":
                return key_input
            if selector == "#url-param-val":
                return val_input
            if selector == "#url-params-result":
                return log
            if selector == "#url-params-table":
                return table
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.params.return_value = "http://example.com?foo=bar"
        self.mock_manager.parse.return_value = {"query_params": {"foo": ["bar"]}}

        # Run
        self.tab.action_param_add()

        # Verify
        self.mock_manager.params.assert_called_with("http://example.com", "add", "foo", "bar")
        # Check if input was updated
        self.assertEqual(url_input.value, "http://example.com?foo=bar")
        # Check inputs cleared
        self.assertEqual(key_input.value, "")
        self.assertEqual(val_input.value, "")

        # Verify Table updated
        table.clear.assert_called()
        table.add_row.assert_called_with("foo", "bar")

    async def test_action_param_remove(self):
        # Mock Inputs
        url_input = MagicMock(spec=Input)
        url_input.value = "http://example.com?foo=bar"
        key_input = MagicMock(spec=Input)
        key_input.value = "foo"
        log = MagicMock(spec=RichLog)
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#url-params-base":
                return url_input
            if selector == "#url-param-key":
                return key_input
            if selector == "#url-params-result":
                return log
            if selector == "#url-params-table":
                return table
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.params.return_value = "http://example.com"
        self.mock_manager.parse.return_value = {"query_params": {}}

        # Run
        self.tab.action_param_remove()

        # Verify
        self.mock_manager.params.assert_called_with("http://example.com?foo=bar", "remove", "foo")
        self.assertEqual(url_input.value, "http://example.com")
        self.assertEqual(key_input.value, "")
        table.clear.assert_called()

    async def test_action_normalize(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "HTTP://EXAMPLE.COM"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#url-norm-input":
                return input_widget
            if selector == "#url-norm-log":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.normalize.return_value = "http://example.com"

        # Run
        self.tab.action_normalize()

        # Verify
        self.mock_manager.normalize.assert_called_with("HTTP://EXAMPLE.COM")
        log.write.assert_called_with("http://example.com")


if __name__ == "__main__":
    unittest.main()
