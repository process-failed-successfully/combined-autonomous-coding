import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path
from main import run_commit
import argparse
import sys

class TestCommitGenerate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_commit_")
        self.project_dir = Path(self.tmp_dir)
        (self.project_dir / ".git").mkdir() # Mock git dir

    def tearDown(self):
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    @patch("main.ask_agent", new_callable=unittest.mock.AsyncMock)
    @patch("subprocess.run")
    @patch("builtins.input")
    @patch("shutil.which")
    async def test_commit_generate(self, mock_which, mock_input, mock_subprocess, mock_ask_agent):
        # Setup mocks
        mock_which.return_value = "/usr/bin/git"

        # Mock git diff --cached output
        diff_output = "diff --git a/test.py b/test.py\n+print('hello')"

        # subprocess.run is called multiple times.
        def subprocess_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = ""
            mock_res.stderr = ""

            if "status" in cmd:
                return mock_res
            if "add" in cmd:
                return mock_res
            if "diff" in cmd and "--quiet" in cmd:
                # Return 1 to indicate changes exist (diff found differences, so quiet exits with 1)
                mock_res.returncode = 1
                return mock_res
            if "diff" in cmd and "--cached" in cmd and "--quiet" not in cmd:
                mock_res.stdout = diff_output
                return mock_res
            if "commit" in cmd:
                mock_res.stdout = "[main 1234567] feat: ai commit"
                return mock_res

            return mock_res

        mock_subprocess.side_effect = subprocess_side_effect

        # Mock user input: 'y' to confirm
        mock_input.return_value = 'y'

        # Mock AI response
        mock_ask_agent.return_value = "feat: add print statement"

        # Prepare args
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message=None,
            run_tests=False,
            generate=True
        )

        # Run
        # run_commit calls sys.exit(0) on success
        with self.assertRaises(SystemExit) as cm:
            await run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify AI was called
        mock_ask_agent.assert_called_once()
        call_args = mock_ask_agent.call_args
        # Keyword args or positional? definition is: query, project_dir...
        # In call: query=prompt
        self.assertIn(diff_output, call_args.kwargs['query'])

        # Verify commit was called with generated message
        commit_call_found = False
        for call in mock_subprocess.call_args_list:
            cmd = call[0][0]
            if "commit" in cmd and "-m" in cmd:
                self.assertIn("feat: add print statement", cmd)
                commit_call_found = True

        self.assertTrue(commit_call_found)

if __name__ == "__main__":
    unittest.main()
