import unittest
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
from pathlib import Path
import json
import collections

from shared.trace_lab import TraceLabManager

class TestTraceLabManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = TraceLabManager(self.project_dir)

    @patch("shutil.which")
    def test_check_availability_success(self, mock_which):
        mock_which.return_value = "/usr/bin/strace"
        manager = TraceLabManager(self.project_dir)
        self.assertTrue(manager.check_availability())

    @patch("shutil.which")
    def test_check_availability_fail(self, mock_which):
        mock_which.return_value = None
        manager = TraceLabManager(self.project_dir)
        self.assertFalse(manager.check_availability())

    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec", new_callable=AsyncMock)
    async def test_run_trace_success(self, mock_exec, mock_which):
        mock_which.return_value = "/usr/bin/strace"
        manager = TraceLabManager(self.project_dir)

        mock_proc = AsyncMock()
        mock_proc.wait.return_value = 0
        mock_exec.return_value = mock_proc

        result = await manager.run_trace(["ls", "-la"], Path("trace.log"))

        self.assertTrue(result)
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        self.assertEqual(args[0], "/usr/bin/strace")
        self.assertIn("trace.log", args)
        self.assertIn("ls", args)

    @patch("shutil.which")
    async def test_run_trace_no_strace(self, mock_which):
        mock_which.return_value = None
        manager = TraceLabManager(self.project_dir)

        # Capture stderr to avoid printing to console during test
        with patch("sys.stderr"):
            result = await manager.run_trace(["ls"], Path("trace.log"))

        self.assertFalse(result)

    def test_analyze_trace_basic(self):
        trace_content = """
1234 openat(AT_FDCWD, "/etc/passwd", O_RDONLY|O_CLOEXEC) = 3
1234 openat(AT_FDCWD, "/etc/shadow", O_RDONLY) = -1 EACCES (Permission denied)
1234 connect(3, {sa_family=AF_INET, sin_port=htons(80), sin_addr=inet_addr("1.2.3.4")}, 16) = 0
1234 read(3, "data", 4) = 4
"""
        with patch("builtins.open", mock_open(read_data=trace_content)):
            with patch.object(Path, "exists", return_value=True):
                analysis = self.manager.analyze_trace(Path("trace.log"))

        self.assertNotIn("error", analysis)
        self.assertIn("/etc/passwd", analysis["files_opened"])
        self.assertEqual(len(analysis["files_failed"]), 1)
        self.assertEqual(analysis["files_failed"][0]["path"], "/etc/shadow")
        self.assertEqual(analysis["files_failed"][0]["error"], "EACCES")
        self.assertIn("1.2.3.4", analysis["network_connects"])
        self.assertEqual(analysis["syscalls"]["openat"], 2)
        self.assertEqual(analysis["syscalls"]["connect"], 1)
        self.assertEqual(analysis["errors"]["EACCES"], 1)

    @patch("shared.trace_lab.AgentClient")
    async def test_explain_trace(self, mock_client_cls):
        mock_client = AsyncMock()
        mock_client.ask_agent.return_value = "The trace shows a permission error accessing /etc/shadow."
        mock_client_cls.return_value = mock_client

        # Mock analyze_trace to return dummy data so we don't need file I/O
        self.manager.analyze_trace = MagicMock(return_value={
            "files_opened": ["/tmp/file"],
            "files_failed": [{"path": "/etc/shadow", "error": "EACCES"}],
            "network_connects": [],
            "syscalls": collections.Counter({"openat": 2}),
            "errors": collections.Counter({"EACCES": 1})
        })

        with patch("builtins.open", mock_open(read_data="dummy trace content")):
             with patch("builtins.print") as mock_print:
                await self.manager.explain_trace(Path("trace.log"))

        mock_client.ask_agent.assert_called_once()
        # Verify print was called with the explanation
        self.assertTrue(any("The trace shows" in str(call) for call in mock_print.call_args_list))

if __name__ == "__main__":
    unittest.main()
