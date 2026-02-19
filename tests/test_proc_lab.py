import asyncio
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from shared.proc_lab import ProcLabManager


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

    @patch("sys.platform", "win32")
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_process(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        mock_proc.wait = AsyncMock()
        mock_proc.terminate = MagicMock()
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("test", "echo test")
        self.assertIn("test", self.manager.processes)

        success = await self.manager.stop_process("test")
        self.assertTrue(success)
        self.assertNotIn("test", self.manager.processes)
        mock_proc.terminate.assert_called_once()

    @patch("sys.platform", "win32")
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_stop_all(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.terminate = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        mock_subprocess.return_value = mock_proc

        await self.manager.start_process("p1", "echo 1")
        await self.manager.start_process("p2", "echo 2")
        self.assertEqual(len(self.manager.processes), 2)

        await self.manager.stop_all()
        self.assertEqual(len(self.manager.processes), 0)

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    async def test_start_processes_cli(self, mock_subprocess):
        # Create distinct mocks for each call
        proc1 = AsyncMock()
        proc1.returncode = None
        proc1.stdout.readline.return_value = b""
        proc1.stderr.readline.return_value = b""

        async def wait_1():
            proc1.returncode = 0
            return None
        proc1.wait.side_effect = wait_1

        proc2 = AsyncMock()
        proc2.returncode = None
        proc2.stdout.readline.return_value = b""
        proc2.stderr.readline.return_value = b""

        async def wait_2():
            proc2.returncode = 0
            return None
        proc2.wait.side_effect = wait_2

        # Side effect iterates through the list for each call
        mock_subprocess.side_effect = [proc1, proc2]

        await self.manager.start_processes(self.procfile)

        self.assertEqual(mock_subprocess.call_count, 2)


if __name__ == "__main__":
    unittest.main()
