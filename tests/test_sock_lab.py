import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import sys
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.sock_lab import SockLabManager, run_sock_lab_logic

class TestSockLab(unittest.IsolatedAsyncioTestCase):
    async def test_start_client(self):
        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_open.return_value = (mock_reader, mock_writer)

            manager = SockLabManager()

            # Patching _interactive_loop to return immediately
            with patch.object(manager, '_interactive_loop', new_callable=AsyncMock) as mock_loop:
                await manager.start_client("localhost", 9000)

                mock_open.assert_called_with("localhost", 9000)
                mock_loop.assert_called_with(mock_reader, mock_writer)

    async def test_start_server(self):
        with patch("asyncio.start_server", new_callable=AsyncMock) as mock_start:
            mock_server = AsyncMock()
            mock_sock = MagicMock()
            mock_sock.getsockname.return_value = ("127.0.0.1", 9000)
            mock_server.sockets = [mock_sock]

            mock_server.__aenter__.return_value = mock_server
            mock_server.__aexit__.return_value = None

            mock_start.return_value = mock_server

            manager = SockLabManager()

            # Mock the future to complete immediately to avoid hanging
            future = asyncio.Future()
            future.set_result(True)

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.create_future.return_value = future

                await manager.start_server("0.0.0.0", 9000)

                mock_start.assert_called()
                args, _ = mock_start.call_args
                self.assertEqual(args[1], "0.0.0.0")
                self.assertEqual(args[2], 9000)

    async def test_interactive_loop_exit(self):
        manager = SockLabManager()
        reader = AsyncMock()
        writer = MagicMock()

        manager.stop_event.set()

        await manager._interactive_loop(reader, writer)

    async def test_cli_logic_connect(self):
        # We need to patch SockLabManager.start_client to ensure it's called
        with patch("shared.sock_lab.SockLabManager.start_client", new_callable=AsyncMock) as mock_client:
            args = MagicMock()
            args.action = "connect"
            args.host = "example.com"
            args.port = 8080

            await run_sock_lab_logic(args)

            mock_client.assert_awaited_with("example.com", 8080)

if __name__ == "__main__":
    unittest.main()
