import unittest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
import asyncio
import os
import sys
from shared.config import Config
from agents.cursor.client import CursorClient

class TestCursorClient(unittest.IsolatedAsyncioTestCase):

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_success(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.model = "test-model"
        config.stream_output = False
        config.timeout = 5
        config.verbose = False
        config.project_dir = MagicMock()

        client = CursorClient(config)

        # Mock process
        process = AsyncMock()
        process.returncode = 0
        process.stdout.readline.side_effect = [b"output line 1\n", b"output line 2\n", b""]
        process.stderr.readline.side_effect = [b""]
        process.wait.return_value = None

        mock_exec.return_value = process

        cwd = MagicMock()
        cwd.resolve.return_value = "/tmp/cwd"

        res = await client.run_command("prompt", cwd)

        self.assertIn("output line 1", res["content"])
        self.assertIn("output line 2", res["content"])

        # Verify args
        mock_exec.assert_called()
        args = mock_exec.call_args[0]
        self.assertEqual(args[0], "cursor-agent")
        self.assertIn("--model", args)
        self.assertIn("test-model", args)

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_timeout(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.timeout = 0.1 # short timeout
        config.project_dir = MagicMock()
        config.stream_output = False
        config.model = None

        client = CursorClient(config)

        process = AsyncMock()
        process.returncode = 0

        # Simulate hang: sleep longer than 5s (the hardcoded wait interval)
        # to ensure asyncio.wait returns with pending tasks
        async def hang():
            await asyncio.sleep(6)
            return b"should not happen"

        process.stdout.readline.side_effect = hang
        process.stderr.readline.side_effect = hang

        mock_exec.return_value = process

        # Mock has_recent_activity to return False to force timeout
        with patch("shared.utils.has_recent_activity", return_value=False):
            # This will take at least 5 seconds due to hardcoded wait(5.0)
            with self.assertRaises(asyncio.TimeoutError):
                await client.run_command("prompt", MagicMock())

        process.kill.assert_called()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_verify_mode(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = True

        client = CursorClient(config)

        res = await client.run_command("prompt", MagicMock())
        self.assertIn("write:output.json", res["content"])
        mock_exec.assert_not_called()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_failure(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.timeout = 5
        config.stream_output = False
        config.model = None

        client = CursorClient(config)

        process = AsyncMock()
        process.returncode = 1
        process.stdout.readline.side_effect = [b""]
        process.stderr.readline.side_effect = [b"error\n", b""]

        mock_exec.return_value = process

        with self.assertRaises(Exception):
            await client.run_command("prompt", MagicMock())

if __name__ == "__main__":
    unittest.main()
