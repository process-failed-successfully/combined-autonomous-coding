import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from shared.sock_lab import SockLabManager

class TestSockLabManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = SockLabManager()

    async def test_start_client_success(self):
        mock_reader = AsyncMock()
        mock_reader.read.side_effect = [b"hello", b""] # Data then EOF
        mock_writer = MagicMock()

        on_data = MagicMock()
        on_error = MagicMock()
        on_connect = MagicMock()

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)) as mock_open:
            await self.manager.start_client("localhost", 8080, on_data, on_error, on_connect)

            mock_open.assert_called_with("localhost", 8080)
            on_connect.assert_called_once()
            on_data.assert_called_with(b"hello")
            # Should error/notify on EOF
            on_error.assert_called_with("Connection closed by remote host.")

    async def test_start_client_fail(self):
        on_data = MagicMock()
        on_error = MagicMock()

        with patch("asyncio.open_connection", side_effect=OSError("Connect failed")):
            await self.manager.start_client("localhost", 8080, on_data, on_error)

            on_error.assert_called()
            self.assertIn("Connect failed", on_error.call_args[0][0])

    async def test_send_data(self):
        self.manager.writer = MagicMock()
        # Mock drain to be awaitable
        self.manager.writer.drain = AsyncMock()

        await self.manager.send_data(b"test")

        self.manager.writer.write.assert_called_with(b"test")
        self.manager.writer.drain.assert_called_once()

    async def test_stop(self):
        self.manager.stop_event = asyncio.Event()
        self.manager.writer = MagicMock()

        self.manager.stop()

        self.assertTrue(self.manager.stop_event.is_set())
        self.manager.writer.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
