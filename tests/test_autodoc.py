import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
import textwrap
from shared.autodoc import AutodocManager

class TestAutodocManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = AutodocManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_structure(self):
        # Create some files
        (self.test_dir / "file1.py").touch()
        (self.test_dir / "subdir").mkdir()
        (self.test_dir / "subdir" / "file2.txt").touch()
        (self.test_dir / ".git").mkdir() # Should be ignored (dotfile)
        (self.test_dir / "__pycache__").mkdir() # Should be ignored

        structure = self.manager.scan_structure(self.test_dir)

        expected_subset = [
            "├── file1.py",
            "└── subdir",
            "    └── file2.txt"
        ]

        for item in expected_subset:
            self.assertIn(item.strip(), structure)

        self.assertNotIn(".git", structure)
        self.assertNotIn("__pycache__", structure)

    def test_scan_commands(self):
        # Create a dummy python file with argparse setup
        dummy_code = textwrap.dedent("""
            import argparse
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers()

            parser_test = subparsers.add_parser("test-cmd", help="A test command")
            parser_alias = subparsers.add_parser("alias-cmd", aliases=["a", "ac"], help="Command with aliases")
        """)

        code_path = self.test_dir / "dummy_main.py"
        code_path.write_text(dummy_code)

        commands = self.manager.scan_commands(code_path)

        self.assertEqual(len(commands), 2)

        # Sort by name is default in scan_commands
        cmd1 = next(c for c in commands if c["name"] == "alias-cmd")
        self.assertEqual(cmd1["help"], "Command with aliases")
        self.assertEqual(cmd1["aliases"], ["a", "ac"])

        cmd2 = next(c for c in commands if c["name"] == "test-cmd")
        self.assertEqual(cmd2["help"], "A test command")

    @patch("shared.autodoc.GeminiAgent")
    async def test_update_readme(self, mock_agent_cls):
        # Setup mock agent
        mock_agent = MagicMock()
        mock_agent.run_agent_session = AsyncMock(return_value=(None, "Updated README Content", None))
        mock_agent_cls.return_value = mock_agent

        # Create dummy main.py for context
        (self.test_dir / "main.py").write_text("import argparse")

        # Create initial README
        (self.test_dir / "README.md").write_text("Old Content")

        # Run update
        success = await self.manager.update_readme(agent_type="gemini")

        self.assertTrue(success)

        # Check if file was updated
        new_content = (self.test_dir / "README.md").read_text()
        self.assertEqual(new_content, "Updated README Content")

        # Check if agent was called
        mock_agent.run_agent_session.assert_called_once()
        args = mock_agent.run_agent_session.call_args[0]
        prompt = args[0]

        self.assertIn("Current Project Structure", prompt)
        self.assertIn("Available CLI Commands", prompt)
        self.assertIn("Current README.md", prompt)

    @patch("shared.autodoc.GeminiAgent")
    async def test_update_readme_check_only(self, mock_agent_cls):
        # Setup mock agent to return DIFFERENT content
        mock_agent = MagicMock()
        mock_agent.run_agent_session = AsyncMock(return_value=(None, "New Content", None))
        mock_agent_cls.return_value = mock_agent

        (self.test_dir / "main.py").write_text("import argparse")
        (self.test_dir / "README.md").write_text("Old Content")

        # Run with check_only=True
        is_uptodate = await self.manager.update_readme(agent_type="gemini", check_only=True)

        self.assertFalse(is_uptodate)

        # File should NOT change
        self.assertEqual((self.test_dir / "README.md").read_text(), "Old Content")

if __name__ == "__main__":
    unittest.main()
