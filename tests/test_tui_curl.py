import unittest
from unittest.mock import patch, MagicMock

from textual.widgets import TextArea
from shared.tui_curl import CurlLabTab


class TestCurlLabTab(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Patch the manager used inside the tab
        self.patcher = patch("shared.tui_curl.CurlLabManager")
        self.MockManager = self.patcher.start()

        self.tab = CurlLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods
        # Mocking app to prevent NoActiveAppError
        mock_app = MagicMock()
        self.tab._app = mock_app
        # We need to mock the app property descriptor or simply monkey-patch it for the instance
        type(self.tab).app = mock_app

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_convert_curl_success(self):
        # Setup mocks
        input_area = MagicMock(spec=TextArea)
        input_area.text = "curl https://example.com"

        py_area = MagicMock(spec=TextArea)
        js_area = MagicMock(spec=TextArea)
        go_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#curl-input-area":
                return input_area
            if selector == "#curl-output-python":
                return py_area
            if selector == "#curl-output-js":
                return js_area
            if selector == "#curl-output-go":
                return go_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Mock manager behavior
        parsed_mock = {"url": "https://example.com", "method": "GET"}
        self.mock_manager.parse_curl.return_value = parsed_mock
        self.mock_manager.to_python_requests.return_value = "python_code"
        self.mock_manager.to_js_fetch.return_value = "js_code"
        self.mock_manager.to_go_http.return_value = "go_code"

        # Run conversion
        self.tab.convert_curl()

        # Verification
        self.mock_manager.parse_curl.assert_called_with("curl https://example.com")
        self.assertEqual(py_area.text, "python_code")
        self.assertEqual(js_area.text, "js_code")
        self.assertEqual(go_area.text, "go_code")
        self.tab.app.notify.assert_called_with("cURL command successfully converted.")

    def test_convert_curl_empty_input(self):
        # Setup mocks
        input_area = MagicMock(spec=TextArea)
        input_area.text = "   "

        def query_side_effect(selector, type=None):
            if selector == "#curl-input-area":
                return input_area
            if selector == "#curl-input-area":
                return input_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Run conversion
        self.tab.convert_curl()

        # Verification
        self.mock_manager.parse_curl.assert_not_called()
        self.tab.app.notify.assert_called_with("cURL command input is required.", severity="error")

    def test_convert_curl_error(self):
        # Setup mocks
        input_area = MagicMock(spec=TextArea)
        input_area.text = "invalid_command"

        def query_side_effect(selector, type=None):
            if selector == "#curl-input-area":
                return input_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Mock manager behavior throwing exception
        self.mock_manager.parse_curl.side_effect = ValueError("Invalid")

        # Run conversion
        self.tab.convert_curl()

        # Verification
        self.tab.app.notify.assert_called_with("Parsing Error: Invalid", severity="error")

    def test_clear_all(self):
        # Setup mocks
        input_area = MagicMock(spec=TextArea)
        py_area = MagicMock(spec=TextArea)
        js_area = MagicMock(spec=TextArea)
        go_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#curl-input-area":
                return input_area
            if selector == "#curl-output-python":
                return py_area
            if selector == "#curl-output-js":
                return js_area
            if selector == "#curl-output-go":
                return go_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Run clear
        self.tab.clear_all()

        # Verification
        self.assertEqual(input_area.text, "")
        self.assertEqual(py_area.text, "")
        self.assertEqual(js_area.text, "")
        self.assertEqual(go_area.text, "")
        self.tab.app.notify.assert_called_with("Fields cleared.")


if __name__ == "__main__":
    unittest.main()
