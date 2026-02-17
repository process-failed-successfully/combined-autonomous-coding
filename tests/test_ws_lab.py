import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys

# Add repo root to path
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.ws_lab import WsLabManager, run_ws_lab_logic

class TestWsLab(unittest.IsolatedAsyncioTestCase):
    async def test_run_simple_connect(self):
        with patch("websockets.connect") as mock_connect:
            # Configure the mock to behave like an async context manager
            mock_ws = AsyncMock()

            connect_context = MagicMock()
            connect_context.__aenter__ = AsyncMock(return_value=mock_ws)
            connect_context.__aexit__ = AsyncMock(return_value=None)

            mock_connect.return_value = connect_context

            manager = WsLabManager()
            await manager.run("ws://example.com")

            mock_connect.assert_called_with("ws://example.com", additional_headers={})

    async def test_run_with_headers(self):
        with patch("websockets.connect") as mock_connect:
            mock_ws = AsyncMock()
            connect_context = MagicMock()
            connect_context.__aenter__ = AsyncMock(return_value=mock_ws)
            connect_context.__aexit__ = AsyncMock(return_value=None)
            mock_connect.return_value = connect_context

            manager = WsLabManager()
            await manager.run("ws://example.com", headers=["Auth: Token", "User-Agent: Test"])

            mock_connect.assert_called_with("ws://example.com", additional_headers={"Auth": "Token", "User-Agent": "Test"})

    async def test_run_send_message(self):
        with patch("websockets.connect") as mock_connect:
            mock_ws = AsyncMock()
            # Mock recv to return a response
            mock_ws.recv.return_value = "response"

            connect_context = MagicMock()
            connect_context.__aenter__ = AsyncMock(return_value=mock_ws)
            connect_context.__aexit__ = AsyncMock(return_value=None)
            mock_connect.return_value = connect_context

            manager = WsLabManager()
            # Non-interactive, send message -> expects response
            await manager.run("ws://example.com", message="hello")

            mock_ws.send.assert_called_with("hello")
            mock_ws.recv.assert_called()

    async def test_cli_logic(self):
        with patch("shared.ws_lab.WsLabManager.run", new_callable=AsyncMock) as mock_run:
            args = MagicMock()
            args.url = "example.com" # Should prepend ws://
            args.header = ["A: B"]
            args.message = "hi"
            args.interactive = False
            args.listen = True
            args.server = False

            await run_ws_lab_logic(args)

            mock_run.assert_called_with("ws://example.com", ["A: B"], "hi", False, True)

    async def test_cli_logic_wss(self):
        with patch("shared.ws_lab.WsLabManager.run", new_callable=AsyncMock) as mock_run:
            args = MagicMock()
            args.url = "wss://secure.com" # Should stay wss://
            args.header = None
            args.message = None
            args.interactive = False
            args.listen = False
            args.server = False

            await run_ws_lab_logic(args)

            mock_run.assert_called_with("wss://secure.com", None, None, False, False)

if __name__ == "__main__":
    unittest.main()
