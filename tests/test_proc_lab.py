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

    def tearDown(self):
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
        # Test CLI plural method
        mock_proc = AsyncMock()
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        # returncode is None initially, then 0 after wait?
        # The loop in start_processes waits for p.wait().
        # We need mock_proc.wait() to eventually finish and we need the loop to exit.
        # If wait returns, the loop continues unless returncode is set.
        # But wait() doesn't set returncode on a mock automatically.

        async def wait_side_effect():
            mock_proc.returncode = 0
            return None

        mock_proc.wait.side_effect = wait_side_effect
        mock_proc.returncode = None

        mock_subprocess.return_value = mock_proc

        # We can't easily wait forever, so we trust it starts and waits.
        # Since we mock wait to return immediately and set returncode, it should finish.
        await self.manager.start_processes(self.procfile)

        self.assertEqual(mock_subprocess.call_count, 2)

if __name__ == "__main__":
    unittest.main()
