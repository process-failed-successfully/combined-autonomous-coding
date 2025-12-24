import unittest
import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from shared.utils import (
    log_startup_config,
    get_file_tree,
    has_recent_activity,
    execute_bash_block,
    execute_write_block,
    execute_read_block,
    execute_search_block,
    process_response_blocks,
    log_system_health,
    generate_agent_id,
)


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.cwd = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_log_startup_config(self):
        config_mock = MagicMock()
        config_mock.agent_type = "test_agent"
        config_mock.project_dir = Path("/tmp")
        config_mock.model = "test_model"
        config_mock.max_iterations = 10
        config_mock.spec_file = "spec.txt"
        config_mock.verbose = True
        config_mock.verify_creation = True

        logger_mock = MagicMock()
        log_startup_config(config_mock, logger_mock)

        # Verify calls
        self.assertTrue(logger_mock.info.called)

    def test_get_file_tree_git(self):
        # Mock subprocess to return git ls-files output
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "file1.py\nfile2.txt"

            tree = get_file_tree(self.test_dir)
            self.assertIn("file1.py", tree)
            self.assertIn("file2.txt", tree)
            self.assertIn("Project Files:", tree)

    def test_get_file_tree_git_truncated(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            # Generate 401 files
            files = "\n".join([f"file{i}.txt" for i in range(401)])
            mock_run.return_value.stdout = files

            tree = get_file_tree(self.test_dir)
            self.assertIn("file0.txt", tree)
            self.assertIn("Truncated first 400", tree)
            self.assertIn("more files", tree)

    def test_get_file_tree_fallback(self):
        # Mock subprocess failure to trigger fallback
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1

            # Create some files
            (self.test_dir / "test.txt").touch()
            (self.test_dir / "subdir").mkdir()
            (self.test_dir / "subdir" / "inner.py").touch()

            tree = get_file_tree(self.test_dir)
            self.assertIn("test.txt", tree)
            self.assertIn("subdir/inner.py", tree)
            self.assertIn("Project Files (System):", tree)

    def test_get_file_tree_fallback_truncated(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1

            # Create many files
            for i in range(401):
                (self.test_dir / f"file{i}.txt").touch()

            tree = get_file_tree(self.test_dir)
            self.assertIn("Truncated first 400", tree)

    def test_has_recent_activity(self):
        # Create a file
        f = self.test_dir / "active.txt"
        f.touch()

        self.assertTrue(has_recent_activity(self.test_dir, seconds=10))

        # Modify mtime to be old
        os.utime(f, (0, 0))
        self.assertFalse(has_recent_activity(self.test_dir, seconds=10))

    def test_has_recent_activity_ignore_patterns(self):
        # Create a log file
        f = self.test_dir / "active.log"
        f.touch()

        # Should be detected without patterns
        self.assertTrue(has_recent_activity(self.test_dir, seconds=10))

        # Should be ignored with patterns
        self.assertFalse(
            has_recent_activity(
                self.test_dir, seconds=10, ignore_patterns=["*.log"]
            )
        )

        # Create a non-ignored file
        f2 = self.test_dir / "active.py"
        f2.touch()
        self.assertTrue(
            has_recent_activity(
                self.test_dir, seconds=10, ignore_patterns=["*.log"]
            )
        )

    async def async_test_execute_bash_block(self):
        # Success case
        output = await execute_bash_block("echo 'hello'", self.test_dir)
        self.assertIn("hello", output)

        # Timeout case
        output = await execute_bash_block("sleep 2", self.test_dir, timeout=0.1)
        self.assertIn("Error: Command timed out", output)

    def test_execute_bash_block_wrapper(self):
        asyncio.run(self.async_test_execute_bash_block())

    def test_execute_write_block(self):
        with patch("shared.telemetry.get_telemetry") as mock_telemetry:
            res = execute_write_block("new_file.txt", "content", self.test_dir)
            self.assertIn("Successfully wrote", res)
            self.assertTrue((self.test_dir / "new_file.txt").exists())
            self.assertEqual((self.test_dir / "new_file.txt").read_text(), "content")
            mock_telemetry.return_value.increment_counter.assert_called_with(
                "files_written_total"
            )

    def test_execute_write_block_error(self):
        # Pass a dir as filename to cause error
        res = execute_write_block("", "content", self.test_dir)
        # Check for Is a directory error
        self.assertTrue("Error" in res or "Is a directory" in res)

    def test_execute_read_block(self):
        f = self.test_dir / "read_me.txt"
        f.write_text("line1\nline2")

        with patch("shared.telemetry.get_telemetry") as mock_telemetry:
            res = execute_read_block("read_me.txt", self.test_dir)
            self.assertIn("line1", res)
            self.assertIn("   1 | line1", res)
            mock_telemetry.return_value.increment_counter.assert_called_with(
                "files_read_total"
            )

    def test_execute_read_block_not_exist(self):
        res = execute_read_block("ghost.txt", self.test_dir)
        self.assertIn("Error: File ghost.txt does not exist", res)

    async def async_test_execute_search_block(self):
        f = self.test_dir / "search.txt"
        f.write_text("needle in haystack")

        output = await execute_search_block("needle", self.test_dir)
        self.assertIn("needle", output)
        self.assertIn("search.txt", output)

        output = await execute_search_block("missing", self.test_dir)
        self.assertIn("No matches found", output)

    def test_execute_search_block_wrapper(self):
        asyncio.run(self.async_test_execute_search_block())

    async def async_test_process_response_blocks(self):
        response_text = """
Some text.
```bash
echo "bash test"
```
More text.
```write: test.txt
written content
```
```read: test.txt
```
"""
        with patch("shared.telemetry.get_telemetry"):
            log, actions = await process_response_blocks(response_text, self.test_dir)

            self.assertIn('Ran Bash: echo "bash test"', actions)
            self.assertIn("Wrote File: test.txt", actions)
            self.assertIn("Read File: test.txt", actions)

            self.assertTrue((self.test_dir / "test.txt").exists())

    def test_process_response_blocks_wrapper(self):
        asyncio.run(self.async_test_process_response_blocks())

    def test_process_response_blocks_project_signed_off(self):
        (self.test_dir / "PROJECT_SIGNED_OFF").touch()
        response_text = """
```bash
echo "should not run"
```
"""

        async def run():
            log, actions = await process_response_blocks(response_text, self.test_dir)
            self.assertNotIn("Ran Bash", actions)
            self.assertIn("Project Signed Off", log)

        asyncio.run(run())

    def test_log_system_health(self):
        # It's hard to mock /proc files in a cross-platform way if not linux,
        # but we can try mocking open.

        with patch("builtins.open", mock_open(read_data="MemAvailable: 100 kB\n")):
            # We need to handle multiple opens, so side_effect is better if we
            # want different contents
            pass

        # Just running it to ensure no crash
        res = log_system_health()
        self.assertIsInstance(res, str)

    def test_generate_agent_id(self):
        aid = generate_agent_id("proj", "spec content", "agent")
        self.assertTrue(aid.startswith("agent_agent_proj_"))

        aid2 = generate_agent_id("proj", "spec content", "agent")
        self.assertEqual(aid, aid2)

        aid3 = generate_agent_id("proj", "diff content", "agent")
        self.assertNotEqual(aid, aid3)


if __name__ == "__main__":
    unittest.main()
