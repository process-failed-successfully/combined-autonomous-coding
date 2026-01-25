import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import asyncio
from shared.process_manager import ServiceManager

class TestServiceManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = ServiceManager(self.project_dir)

    def test_add_service(self):
        self.manager.add_service("test", "echo 'hello'")
        self.assertIn("test", self.manager.services)
        self.assertEqual(self.manager.services["test"].command, "echo 'hello'")

    async def test_start_service(self):
        # Create a Mock Process
        mock_process = MagicMock()
        mock_process.pid = 1234

        # Configure stdout
        mock_stdout = AsyncMock()
        mock_stdout.readline.side_effect = [b"line1\n", b"line2\n", b""]
        mock_process.stdout = mock_stdout

        # Configure wait
        mock_process.wait = AsyncMock()
        mock_process.wait.return_value = 0
        mock_process.returncode = 0

        # Patch creation
        with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_process

            self.manager.add_service("test", "echo 'hello'")
            await self.manager.start_service("test")

            # Check if process created
            mock_create.assert_called_once()
            service = self.manager.get_service("test")
            self.assertEqual(service.status, "Running")
            self.assertEqual(service.pid, 1234)

            # Wait a bit for output reader task
            await asyncio.sleep(0.1)

            # Since output reader is background task, we check buffer
            self.assertIn("line1", service.output_buffer)
            self.assertIn("line2", service.output_buffer)

    async def test_stop_service(self):
        # Create a Mock Process
        mock_process = MagicMock()
        mock_process.pid = 1234

        # Configure wait
        mock_process.wait = AsyncMock()
        mock_process.wait.return_value = None

        # Configure terminate (sync)
        mock_process.terminate = MagicMock()

        # Configure stdout (none for stop test)
        mock_process.stdout = None

        with patch("asyncio.create_subprocess_shell", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_process

            self.manager.add_service("test", "sleep 10")
            await self.manager.start_service("test")

            service = self.manager.get_service("test")
            self.assertEqual(service.status, "Running")

            # Stop
            await self.manager.stop_service("test")

            # Verify terminate called
            mock_process.terminate.assert_called_once()
            self.assertEqual(service.status, "Stopped")
            self.assertIsNone(service.pid)

if __name__ == "__main__":
    unittest.main()
