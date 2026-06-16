import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from textual.widgets import Label, TextArea

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_redis import RedisLabTab  # noqa: E402


class RedisLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield RedisLabTab(Path("."))


class TestRedisLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_connect_flow(self):
        with patch('shared.tui_redis.RedisLabManager') as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.connect = MagicMock(return_value=True)
            mock_instance.scan_keys = MagicMock(return_value=["key1", "key2"])

            app = RedisLabTestApp()

            async with app.run_test() as pilot:
                # Click Connect
                pilot.app.query_one("#btn-redis-connect").press()
                await pilot.pause()

                # Check status label
                status_lbl = app.query_one("#lbl-redis-status", Label)
                # renderable might be Rich text, convert to str
                assert "Connected" in str(status_lbl.renderable)

                # Verify scan keys called
                mock_instance.scan_keys.assert_called()

    async def test_load_and_save_key(self):
        with patch('shared.tui_redis.RedisLabManager') as MockManager:
            mock_instance = MockManager.return_value
            # Setup data
            mock_instance.get_type.return_value = "string"
            mock_instance.get_ttl.return_value = 100
            mock_instance.get_value.return_value = "initial_value"
            mock_instance.set.return_value = True

            app = RedisLabTestApp()

            async with app.run_test() as pilot:
                tab = app.query_one(RedisLabTab)

                # Simulate loading a key programmatically (easier than list selection in test)
                await tab.load_key("test_key")

                # Verify Editor content
                editor = app.query_one("#redis-value-editor", TextArea)
                assert editor.text == "initial_value"

                # Verify Labels
                assert str(app.query_one("#lbl-redis-type", Label).renderable) == "string"
                assert str(app.query_one("#lbl-redis-ttl", Label).renderable) == "100"

                # Modify and Save
                editor.text = "new_value"
                pilot.app.query_one("#btn-redis-save").press()
                await pilot.pause()

                # Verify set called
                mock_instance.set.assert_called_with("test_key", "new_value")
