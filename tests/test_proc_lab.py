import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from shared.proc_lab import ProcLabManager, run_proc_lab_logic
import argparse
import sys

class TestProcLab(unittest.TestCase):
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
    def test_start_processes(self, mock_subprocess):
        # Mock process
        mock_proc = AsyncMock()
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        mock_proc.wait = AsyncMock()
        mock_subprocess.return_value = mock_proc

        async def run():
            await self.manager.start_processes(self.procfile)

        asyncio.run(run())

        self.assertEqual(mock_subprocess.call_count, 2) # web and worker

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    def test_start_specific_process(self, mock_subprocess):
        # Mock process
        mock_proc = AsyncMock()
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        mock_proc.wait = AsyncMock()
        mock_subprocess.return_value = mock_proc

        async def run():
            await self.manager.start_processes(self.procfile, specific_process="web")

        asyncio.run(run())

        self.assertEqual(mock_subprocess.call_count, 1)
        args, _ = mock_subprocess.call_args
        self.assertEqual(args[0], "echo web")

    def test_list_processes(self):
        self.manager.list_processes(self.procfile)

    @patch("os.killpg")
    @patch("os.getpgid")
    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    def test_start_stop_process(self, mock_subprocess, mock_getpgid, mock_killpg):
        mock_proc = AsyncMock()
        mock_proc.pid = 1234
        mock_proc.stdout.readline.return_value = b""
        mock_proc.stderr.readline.return_value = b""
        mock_proc.returncode = None

        # Setup mock for getpgid to return something valid-looking
        mock_getpgid.return_value = 1234

        async def wait_side_effect():
            mock_proc.returncode = 0
            return 0

        mock_proc.wait.side_effect = wait_side_effect
        mock_subprocess.return_value = mock_proc

        async def run():
            self.manager.load_config(self.procfile)
            await self.manager.start_process("web")
            self.assertIn("web", self.manager.processes)

            await self.manager.stop_process("web")
            self.assertNotIn("web", self.manager.processes)

        asyncio.run(run())

    @patch("asyncio.create_subprocess_shell", new_callable=AsyncMock)
    def test_output_callback(self, mock_subprocess):
        mock_proc = AsyncMock()
        mock_proc.stdout.readline.side_effect = [b"line1\n", b"line2\n", b""]
        mock_proc.stderr.readline.return_value = b""
        mock_subprocess.return_value = mock_proc

        captured = []
        def on_output(name, line):
            captured.append((name, line))

        async def run():
            self.manager.load_config(self.procfile)
            await self.manager.start_process("web", on_output=on_output)
            # Give the background tasks a moment to process the mock stream
            await asyncio.sleep(0.01)

        asyncio.run(run())

        # Verify callback was called
        # Note: the order depends on how tasks are scheduled, but we check presence
        self.assertTrue(len(captured) >= 2)
        lines = [c[1] for c in captured]
        self.assertIn("line1", lines)
        self.assertIn("line2", lines)

if __name__ == "__main__":
    unittest.main()
