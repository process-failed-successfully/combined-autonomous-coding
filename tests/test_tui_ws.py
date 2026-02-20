import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Button, Input, Label, RichLog, Checkbox  # noqa: E402
from shared.tui_ws import WsLabTab  # noqa: E402


class TestWsLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_compose(self):
        tab = WsLabTab()
        self.assertIsInstance(tab, WsLabTab)
        # We can't easily test compose without an App, but we can check if methods exist
        self.assertTrue(hasattr(tab, "connect"))
        self.assertTrue(hasattr(tab, "disconnect"))

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_connect_success(self, mock_connect):
        tab = WsLabTab()

        # Mock UI widgets
        mock_input_url = MagicMock(spec=Input)
        mock_input_url.value = "ws://test.com"

        mock_btn_connect = MagicMock(spec=Button)
        mock_btn_disconnect = MagicMock(spec=Button)
        mock_btn_send = MagicMock(spec=Button)
        mock_lbl_status = MagicMock(spec=Label)
        mock_log = MagicMock(spec=RichLog)
        mock_chk = MagicMock(spec=Checkbox)
        mock_chk.value = False

        # Mock query_one
        def query_side_effect(selector, type=None):
            if selector == "#ws-url":
                return mock_input_url
            if selector == "#btn-ws-connect":
                return mock_btn_connect
            if selector == "#btn-ws-disconnect":
                return mock_btn_disconnect
            if selector == "#btn-ws-send":
                return mock_btn_send
            if selector == "#lbl-ws-status":
                return mock_lbl_status
            if selector == "#ws-log":
                return mock_log
            if selector == "#chk-ws-autoscroll":
                return mock_chk
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        # Mock websocket instance
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws

        # Mock receive_loop to avoid indefinite running
        # We replace the method on the instance
        tab.receive_loop = AsyncMock()

        await tab.connect()

        mock_connect.assert_called_with("ws://test.com")
        self.assertTrue(tab.is_connected)
        self.assertIsNotNone(tab.websocket)

    @patch("websockets.connect", new_callable=AsyncMock)
    async def test_send_message(self, mock_connect):
        tab = WsLabTab()
        tab.is_connected = True

        mock_ws = AsyncMock()
        tab.websocket = mock_ws

        # Mock UI
        mock_input_msg = MagicMock(spec=Input)
        mock_input_msg.value = "Hello"
        mock_log = MagicMock(spec=RichLog)
        mock_chk = MagicMock(spec=Checkbox)
        mock_chk.value = True

        def query_side_effect(selector, type=None):
            if selector == "#ws-input-msg":
                return mock_input_msg
            if selector == "#ws-log":
                return mock_log
            if selector == "#chk-ws-autoscroll":
                return mock_chk
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        await tab.send_message()

        mock_ws.send.assert_called_with("Hello")
        mock_log.write.assert_called()

    async def test_disconnect(self):
        tab = WsLabTab()
        tab.is_connected = True
        mock_ws = AsyncMock()
        tab.websocket = mock_ws

        # Real task
        async def dummy_task():
            pass
        real_task = asyncio.create_task(dummy_task())
        # Mock cancel to verify call
        real_task.cancel = MagicMock(side_effect=real_task.cancel)
        tab.recv_task = real_task

        # Mock UI
        mock_btn_connect = MagicMock(spec=Button)
        mock_btn_disconnect = MagicMock(spec=Button)
        mock_btn_send = MagicMock(spec=Button)
        mock_lbl_status = MagicMock(spec=Label)
        mock_log = MagicMock(spec=RichLog)
        mock_chk = MagicMock(spec=Checkbox)

        def query_side_effect(selector, type=None):
            if selector == "#btn-ws-connect":
                return mock_btn_connect
            if selector == "#btn-ws-disconnect":
                return mock_btn_disconnect
            if selector == "#btn-ws-send":
                return mock_btn_send
            if selector == "#lbl-ws-status":
                return mock_lbl_status
            if selector == "#ws-log":
                return mock_log
            if selector == "#chk-ws-autoscroll":
                return mock_chk
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        await tab.disconnect()

        mock_ws.close.assert_called()
        self.assertFalse(tab.is_connected)
        self.assertIsNone(tab.websocket)
        # Check task cancellation on the original object
        real_task.cancel.assert_called()


if __name__ == "__main__":
    unittest.main()
