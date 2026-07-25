import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys
import aiohttp

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.sse_lab import SSELabManager, run_sse_lab_logic

class TestSSELab(unittest.IsolatedAsyncioTestCase):
    async def test_listen_success(self):
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200

            # Mock async iterator for content
            async def mock_content():
                yield b"data: test message 1\n"
                yield b"event: update\n"
                yield b"id: 123\n"
                yield b"retry: 5000\n"
                yield b"\n"

            mock_response.content = mock_content()

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_get.return_value = mock_ctx

            manager = SSELabManager()
            await manager.listen("http://test.local")

            mock_get.assert_called_with("http://test.local")

    async def test_listen_error_status(self):
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__.return_value = mock_response
            mock_get.return_value = mock_ctx

            manager = SSELabManager()
            # This should just print an error and return
            await manager.listen("http://test.local")

    @patch("shared.sse_lab.SSELabManager.listen", new_callable=AsyncMock)
    async def test_cli_logic_normal(self, mock_listen):
        args = MagicMock()
        args.tui = False
        args.url = "http://example.com"
        args.header = ["Auth: Token"]

        await run_sse_lab_logic(args)
        mock_listen.assert_called_with("http://example.com", {"Auth": "Token"})

    @patch("main.run_tui")
    async def test_cli_logic_tui(self, mock_run_tui):
        args = MagicMock()
        args.tui = True

        await run_sse_lab_logic(args)
        mock_run_tui.assert_called_with(args, start_tab='sse')

if __name__ == "__main__":
    unittest.main()
