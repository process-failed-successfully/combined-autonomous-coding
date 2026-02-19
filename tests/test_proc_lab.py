import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
import sys
import os
from shared.proc_lab import ProcLabManager

# Helper class to mock asyncio.subprocess.Process behavior reliably
class MockProcess:
    def __init__(self, name="proc"):
        self.name = name
        self.returncode = None
        self.stdout = AsyncMock()
        self.stderr = AsyncMock()
        # Ensure readline returns EOF immediately to avoid blocking stream reading
        self.stdout.readline.return_value = b""
        self.stderr.readline.return_value = b""
        self.pid = 12345

    async def wait(self):
        # Simulate process finishing
        self.returncode = 0
        return None

    def terminate(self):
        pass

    def kill(self):
        pass

class TestProcLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.procfile = self.test_dir / "Procfile"
        self.procfile.write_text("web: echo web\nworker: echo worker\n#comment\n")
        self.manager = ProcLabManager(self.test_dir)

    async def asyncTearDown(self):
        # Ensure any lingering tasks or processes are cleaned up
        await self.manager.stop_all()
        if self.test_dir.exists():
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
        mock_proc = MockProcess("test")
        # Mock readline to return some content then EOF
        mock_proc.stdout.readline.side_effect = [b"line1\n", b""]
        mock_subprocess.return_value = mock_proc

        callback = MagicMock()
        success = await self.manager.start_process("test", "echo test", log_callback=callback)

        self.assertTrue(success)
        self.assertIn("test", self.manager.processes)

        # Give asyncio tasks a moment to run
        await asyncio.sleep(0.01)

        callback.assert_called_with("test", "line1")

    @patch("os.killpg")
    @patch("os.getpgid")
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_process(self, mock_subprocess, mock_getpgid, mock_killpg):
        mock_proc = MockProcess("test")
        mock_proc.terminate = MagicMock()
        mock_subprocess.return_value = mock_proc
        # Mock getpgid to return a PID
        mock_getpgid.return_value = 12345

        await self.manager.start_process("test", "echo test")
        self.assertIn("test", self.manager.processes)

        success = await self.manager.stop_process("test")
        self.assertTrue(success)
        self.assertNotIn("test", self.manager.processes)

        if sys.platform != "win32":
            mock_killpg.assert_called_once()
        else:
            mock_proc.terminate.assert_called_once()

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_all(self, mock_subprocess):
        mock_proc = MockProcess("p1")
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("p1", "echo 1")
        await self.manager.start_process("p2", "echo 2")
        self.assertEqual(len(self.manager.processes), 2)

        await self.manager.stop_all()
        self.assertEqual(len(self.manager.processes), 0)

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_processes_cli(self, mock_subprocess):
        # Create distinct mocks for each process
        p1 = MockProcess("web")
        p2 = MockProcess("worker")

        # Return p1 then p2
        mock_subprocess.side_effect = [p1, p2]

        # Use wait_for to prevent infinite hang if logic fails
        try:
            await asyncio.wait_for(self.manager.start_processes(self.procfile), timeout=5.0)
        except asyncio.TimeoutError:
            self.fail("start_processes timed out (infinite loop detected)")

        self.assertEqual(mock_subprocess.call_count, 2)

if __name__ == "__main__":
    unittest.main()
