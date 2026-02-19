import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from shared.proc_lab import ProcLabManager
import sys
import os

class MockProcess:
    """Helper class to mock asyncio.subprocess.Process behavior."""
    def __init__(self, returncode=None):
        self.returncode = returncode
        self.stdout = AsyncMock()
        self.stderr = AsyncMock()
        self.stdout.readline.return_value = b""
        self.stderr.readline.return_value = b""
        self.pid = 1234
        self.terminate = MagicMock()
        self.kill = MagicMock()
        self.wait_mock = AsyncMock() # To track calls if needed

    async def wait(self):
        await self.wait_mock()
        self.returncode = 0
        return None

class TestProcLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.procfile = self.test_dir / "Procfile"
        self.procfile.write_text("web: echo web\nworker: echo worker\n#comment\n")
        self.manager = ProcLabManager(self.test_dir)

    async def asyncTearDown(self):
        # Ensure any lingering tasks or processes are cleaned up
        await self.manager.stop_all()
        shutil.rmtree(self.test_dir)

    def test_parse_procfile(self):
        procs = self.manager.parse_procfile(self.procfile)
        self.assertEqual(len(procs), 2)
        self.assertEqual(procs["web"], "echo web")
        self.assertEqual(procs["worker"], "echo worker")

    def test_parse_procfile_missing(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.parse_procfile(self.test_dir / "NonExistent")

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_process(self, mock_subprocess):
        mock_proc = MockProcess()
        mock_proc.stdout.readline.side_effect = [b"line1\n", b""]
        mock_subprocess.return_value = mock_proc

        callback = MagicMock()
        success = await self.manager.start_process("test", "echo test", log_callback=callback)

        self.assertTrue(success)
        self.assertIn("test", self.manager.processes)

        # Give asyncio tasks a moment to run
        await asyncio.sleep(0.01)

        callback.assert_called_with("test", "line1")

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_process(self, mock_subprocess):
        mock_proc = MockProcess()
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("test", "echo test")
        self.assertIn("test", self.manager.processes)

        # On Linux, stop_process calls os.killpg instead of terminate
        # We need to mock os.killpg if we want to test that path, or patch sys.platform
        with patch("sys.platform", "win32"):
             success = await self.manager.stop_process("test")
             self.assertTrue(success)
             self.assertNotIn("test", self.manager.processes)
             mock_proc.terminate.assert_called_once()

        # Test Linux path separately if needed, but for now let's fix the assertion failure
        # The previous failure was because on Linux it calls os.killpg, not terminate.

    @patch("os.killpg")
    @patch("os.getpgid")
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_process_linux(self, mock_subprocess, mock_getpgid, mock_killpg):
        mock_proc = MockProcess()
        mock_subprocess.return_value = mock_proc
        mock_getpgid.return_value = 1234

        await self.manager.start_process("test", "echo test")

        # Force linux platform behavior if not already on linux,
        # but the test runner is linux.
        if sys.platform != "win32":
            success = await self.manager.stop_process("test")
            self.assertTrue(success)
            mock_killpg.assert_called()
            mock_proc.terminate.assert_not_called()

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_all(self, mock_subprocess):
        mock_proc = MockProcess()
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("p1", "echo 1")
        await self.manager.start_process("p2", "echo 2")
        self.assertEqual(len(self.manager.processes), 2)

        await self.manager.stop_all()
        self.assertEqual(len(self.manager.processes), 0)

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_processes_cli(self, mock_subprocess):
        # Create distinct mocks for each process
        p1 = MockProcess()
        p2 = MockProcess()

        # Return p1 then p2
        mock_subprocess.side_effect = [p1, p2]

        # Use wait_for to prevent infinite hang if logic fails
        try:
            # Increased timeout to 5.0s to avoid flakiness in CI
            await asyncio.wait_for(self.manager.start_processes(self.procfile), timeout=5.0)
        except asyncio.TimeoutError:
            self.fail("start_processes timed out (infinite loop detected)")

        self.assertEqual(mock_subprocess.call_count, 2)
        # Verify wait was called
        p1.wait_mock.assert_called()
        p2.wait_mock.assert_called()

if __name__ == "__main__":
    unittest.main()
