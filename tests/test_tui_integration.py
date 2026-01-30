import unittest
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
from shared.tui import TUIStream, ApiLabTab
from pathlib import Path
import asyncio

class TestTUIIntegration(unittest.IsolatedAsyncioTestCase):
    def test_tui_stream(self):
        mock_log = MagicMock()
        mock_app = MagicMock()
        stream = TUIStream(mock_log, mock_app)

        # Test normal write
        stream.write("  Indented Text\n")
        mock_app.call_from_thread.assert_called_once()
        args = mock_app.call_from_thread.call_args
        func, text = args[0]
        self.assertEqual(func, mock_log.write)
        self.assertEqual(text, "  Indented Text")

        # Test empty write
        mock_app.reset_mock()
        stream.write("")
        mock_app.call_from_thread.assert_not_called()

        # Test whitespace only write
        mock_app.reset_mock()
        stream.write("   ")
        mock_app.call_from_thread.assert_not_called()

        # Test newline only write
        mock_app.reset_mock()
        stream.write("\n")
        mock_app.call_from_thread.assert_not_called()

    @patch("shared.tui.ApiLabManager")
    def test_api_lab_tab_methods(self, mock_manager_cls):
        # Setup mock manager instance
        mock_manager = mock_manager_cls.return_value
        mock_manager.spec_data = {}

        tab = ApiLabTab(Path("."))

        # Check if run_fuzzer is defined
        self.assertTrue(hasattr(tab, "run_fuzzer"))
        self.assertTrue(callable(tab.run_fuzzer))

        # Check if on_button_pressed handles the new button
        self.assertTrue(hasattr(tab, "on_button_pressed"))

    @patch("shared.tui.ApiLabManager")
    @patch("shared.tui.TUIStream")
    @patch("asyncio.to_thread")
    async def test_run_fuzzer(self, mock_to_thread, mock_tui_stream_cls, mock_manager_cls):
        # Setup mocks
        mock_manager = mock_manager_cls.return_value

        # Mock query_one to return values for inputs
        tab = ApiLabTab(Path("."))

        # Mock query_one
        def query_one_side_effect(selector, type=None):
            mock_widget = MagicMock()
            if selector == "#api-method":
                mock_widget.value = "GET"
            elif selector == "#api-url":
                mock_widget.value = "http://test.com"
            elif selector == "#api-fuzzer-log":
                mock_widget.write = MagicMock()
                mock_widget.clear = MagicMock()
            elif selector == "#btn-api-fuzz":
                mock_widget.disabled = False
            return mock_widget

        tab.query_one = MagicMock(side_effect=query_one_side_effect)
        tab.notify = MagicMock()

        # Mock asyncio.to_thread to return immediate result
        mock_to_thread.return_value = [
            {"payload": {}, "status": 200, "crash": False},
            {"payload": {"bad": "data"}, "status": 500, "crash": True}
        ]

        # Mock app property
        with patch("shared.tui.ApiLabTab.app", new_callable=PropertyMock) as mock_app_prop:
            mock_app_prop.return_value = MagicMock()

            # Run fuzzer
            await tab.run_fuzzer()

        # Verify TUIStream created
        mock_tui_stream_cls.assert_called()

        # Verify to_thread called
        mock_to_thread.assert_called()

        # Verify log writes (checking if crash was logged)
        # Note: Since we mocked query_one, we can't easily check what was written to the mocked log widget
        # unless we capture the mock returned by query_one.
        # But we can verify notify was called
        tab.notify.assert_called()

        # Verify button re-enabled
        # The disabled property is set on the mock returned by query_one
        # We can check if query_one was called for the button
        tab.query_one.assert_any_call("#btn-api-fuzz")

if __name__ == "__main__":
    unittest.main()
