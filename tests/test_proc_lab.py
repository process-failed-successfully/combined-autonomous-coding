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
        # Side effect for readline must be an iterable of awaitables or return awaitables?
        # AsyncMock side_effect with list returns items one by one.
        # But readline is async, so it returns a coroutine.
        # Standard AsyncMock handles 'await mock()' but 'await mock.readline()' needs configuration.

        # We need mock_proc.stdout.readline() to be awaited and return bytes.

        async def mock_readline_gen(lines):
            for line in lines:
                yield line
            while True:
                yield b""

        # Simplification: just return empty bytes immediately to terminate loop
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
        # Just ensure it runs without error (prints to stdout)
        # We could capture stdout to verify output but basic execution is enough for now
        self.manager.list_processes(self.procfile)

if __name__ == "__main__":
    unittest.main()
