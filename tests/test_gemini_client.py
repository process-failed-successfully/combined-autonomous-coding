import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from shared.config import Config
from agents.gemini.client import GeminiClient


class TestGeminiClient(unittest.IsolatedAsyncioTestCase):

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_success(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.model = "auto"
        config.stream_output = False
        config.timeout = 5
        config.verbose = False
        config.project_dir = MagicMock()

        client = GeminiClient(config)

        process = AsyncMock()
        process.returncode = 0
        process.stdout.readline.side_effect = [b"output\n", b""]
        process.stderr.readline.side_effect = [b""]
        process.wait.return_value = None

        # Stdin mock
        process.stdin = AsyncMock()
        process.stdin.write = MagicMock()
        process.stdin.drain = AsyncMock()
        process.stdin.close = MagicMock()

        mock_exec.return_value = process

        res = await client.run_command("prompt", MagicMock())

        self.assertIn("output", res["content"])
        mock_exec.assert_called()
        process.stdin.write.assert_called_with(b"prompt")

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_timeout(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.timeout = 0.1
        config.project_dir = MagicMock()
        config.stream_output = False
        config.model = "test-model"

        client = GeminiClient(config)

        process = AsyncMock()
        process.returncode = 0
        process.stdin = AsyncMock()

        # Simulate hang longer than 5s
        async def hang():
            await asyncio.sleep(6)
            return b"nope"

        process.stdout.readline.side_effect = hang
        process.stderr.readline.side_effect = hang

        # Fix process.kill to be a Mock (sync) instead of AsyncMock
        process.kill = MagicMock()

        mock_exec.return_value = process

        with patch("shared.utils.has_recent_activity", return_value=False):
            with self.assertRaises(asyncio.TimeoutError):
                await client.run_command("prompt", MagicMock())

        process.kill.assert_called()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_verify_mode(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = True

        client = GeminiClient(config)

        res = await client.run_command("prompt", MagicMock())
        self.assertIn(
            "write:output.json", res["candidates"][0]["content"]["parts"][0]["text"]
        )
        mock_exec.assert_not_called()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_command_failure(self, mock_exec):
        config = MagicMock(spec=Config)
        config.verify_creation = False
        config.timeout = 5
        config.stream_output = False
        config.model = "auto"

        client = GeminiClient(config)

        process = AsyncMock()
        process.returncode = 1
        process.stdin = AsyncMock()
        process.stdout.readline.side_effect = [b""]
        process.stderr.readline.side_effect = [b"error\n", b""]

        mock_exec.return_value = process

        # It logs error but returns content?
        # No, check code: if process.returncode != 0: logs error.
        # But doesn't raise exception unless `process` creation failed or timeout.
        # It returns `{"content": stdout_text}` even on error?
        # shared/agent_client.py doesn't check returncode?
        # gemini/client.py: "if process.returncode != 0: logger.error..."
        # Then it returns content.

        # Wait, if execute_bash_block or others fail, they return error string.
        # But here run_command captures output.
        # If gemini fails, stdout might be empty.

        res = await client.run_command("prompt", MagicMock())
        self.assertEqual(res["content"], "")


if __name__ == "__main__":
    unittest.main()
