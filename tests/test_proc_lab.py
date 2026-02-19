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

        # Patch sys.platform to 'linux' to force the os.killpg path
        with patch('sys.platform', 'linux'):
            # Must mock os.getpgid and os.killpg
            with patch('os.getpgid') as mock_getpgid, \
                 patch('os.killpg') as mock_killpg:

                mock_proc.pid = 123
                mock_getpgid.return_value = 123  # return pgid

                success = await self.manager.stop_process("test")

                self.assertTrue(success)
                self.assertNotIn("test", self.manager.processes)
                mock_getpgid.assert_called_with(123)
                mock_killpg.assert_called()

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_all(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        # Provide a pid for killpg
        mock_proc.pid = 123
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("p1", "echo 1")
        await self.manager.start_process("p2", "echo 2")
        self.assertEqual(len(self.manager.processes), 2)

        with patch('sys.platform', 'linux'):
            with patch('os.getpgid') as mock_getpgid, \
                 patch('os.killpg') as mock_killpg:

                mock_getpgid.return_value = 123
                await self.manager.stop_all()

                self.assertEqual(mock_getpgid.call_count, 2)
                self.assertEqual(mock_killpg.call_count, 2)

        self.assertEqual(len(self.manager.processes), 0)

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_processes_cli(self, mock_subprocess):
        # Create distinct mocks for each process call

        # Mock 1
        mock_proc1 = AsyncMock()
        mock_proc1.stdout.readline.return_value = b""
        mock_proc1.stderr.readline.return_value = b""
        mock_proc1.returncode = None
        mock_proc1.pid = 101

        async def wait_side_effect1():
            mock_proc1.returncode = 0
            return None
        mock_proc1.wait.side_effect = wait_side_effect1

        # Mock 2
        mock_proc2 = AsyncMock()
        mock_proc2.stdout.readline.return_value = b""
        mock_proc2.stderr.readline.return_value = b""
        mock_proc2.returncode = None
        mock_proc2.pid = 102

        async def wait_side_effect2():
            mock_proc2.returncode = 0
            return None
        mock_proc2.wait.side_effect = wait_side_effect2

        # Return them in sequence
        mock_subprocess.side_effect = [mock_proc1, mock_proc2]

        with patch('sys.platform', 'linux'):
            await self.manager.start_processes(self.procfile)

        self.assertEqual(mock_subprocess.call_count, 2)

if __name__ == "__main__":
    unittest.main()
