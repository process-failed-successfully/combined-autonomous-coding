import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from shared.proc_lab import ProcLabManager, run_proc_lab_logic
import argparse
import sys

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
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.stdout.readline.side_effect = [b"line1\n", b""]
        mock_proc.stderr.readline.return_value = b""
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
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.wait = AsyncMock()
        mock_proc.terminate = MagicMock()
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("test", "echo test")
        self.assertIn("test", self.manager.processes)

        success = await self.manager.stop_process("test")
        self.assertTrue(success)
        self.assertNotIn("test", self.manager.processes)
        mock_proc.terminate.assert_called_once()

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_all(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("p1", "echo 1")
        await self.manager.start_process("p2", "echo 2")
        self.assertEqual(len(self.manager.processes), 2)

        await self.manager.stop_all()
        self.assertEqual(len(self.manager.processes), 0)

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_processes_cli(self, mock_subprocess):
        # Create distinct mocks for each process
        p1 = AsyncMock()
        p1.stdout.readline.return_value = b""
        p1.stderr.readline.return_value = b""
        p1.returncode = None

        async def wait_p1():
            # Explicitly set returncode on the mock object
            p1.returncode = 0
            return None
        p1.wait.side_effect = wait_p1

        p2 = AsyncMock()
        p2.stdout.readline.return_value = b""
        p2.stderr.readline.return_value = b""
        p2.returncode = None

        async def wait_p2():
            # Explicitly set returncode on the mock object
            p2.returncode = 0
            return None
        p2.wait.side_effect = wait_p2

        # Return p1 then p2
        mock_subprocess.side_effect = [p1, p2]

        # Use wait_for to prevent infinite hang if logic fails
        try:
            # Increased timeout to 5.0s to avoid flakiness in CI
            await asyncio.wait_for(self.manager.start_processes(self.procfile), timeout=5.0)
        except asyncio.TimeoutError:
            self.fail("start_processes timed out (infinite loop detected)")

        self.assertEqual(mock_subprocess.call_count, 2)

if __name__ == "__main__":
    unittest.main()
