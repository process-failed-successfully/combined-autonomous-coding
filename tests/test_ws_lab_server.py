import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from shared.ws_lab import WsLabManager

class TestWsLabServer(unittest.IsolatedAsyncioTestCase):
    async def test_serve_starts_server(self):
        manager = WsLabManager()
        port = 9000

        # Mock websockets.serve to return an async context manager
        mock_serve_cm = AsyncMock()
        mock_serve_cm.__aenter__.return_value = None
        mock_serve_cm.__aexit__.return_value = None

        mock_serve = MagicMock(return_value=mock_serve_cm)

        async def stop_later():
            await asyncio.sleep(0.01)
            manager.stop_event.set()

        with patch("websockets.serve", mock_serve):
            # Run serve and stop in parallel
            await asyncio.gather(
                manager.serve(port),
                stop_later()
            )

        mock_serve.assert_called_once_with(manager._handler, "0.0.0.0", port)

    async def test_handler_broadcast(self):
        manager = WsLabManager()

        # Mock client 1: Sends a message
        client1 = MagicMock()
        client1.remote_address = ("127.0.0.1", 1000)
        client1.send = AsyncMock()
        client1.close = AsyncMock()

        # Setup async iterator for client1 messages
        # MagicMock.__aiter__ iterates over the return_value if it's an iterable
        client1.__aiter__.return_value = ["Hello"]

        # Mock client 2: Receives the message
        client2 = MagicMock()
        client2.remote_address = ("127.0.0.1", 2000)
        client2.send = AsyncMock()

        # Pre-add client2 to connected clients to simulate it being already connected
        manager.connected_clients.add(client2)

        # Run handler for client1
        await manager._handler(client1)

        # Verify client2 received broadcast
        # Format: "[('127.0.0.1', 1000)] Hello"
        expected_msg = "[('127.0.0.1', 1000)] Hello"
        client2.send.assert_called_with(expected_msg)

        # Client1 should be removed from set (it finished iteration/disconnected)
        self.assertNotIn(client1, manager.connected_clients)

        # Client1 should NOT receive the broadcast (it sent it)
        client1.send.assert_not_called()

if __name__ == "__main__":
    unittest.main()
