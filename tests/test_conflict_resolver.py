
import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from shared.conflict_resolver import ConflictResolver


class TestConflictResolver(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.resolver = ConflictResolver(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_find_conflicted_files(self):
        # Create a file with conflicts
        conflicted_file = self.test_dir / "conflict.py"
        conflicted_file.write_text("""
<<<<<<< HEAD
print("Hello World")
=======
print("Hello Universe")
>>>>>>> feature-branch
""")

        # Create a clean file
        clean_file = self.test_dir / "clean.py"
        clean_file.write_text('print("Clean")')

        files = self.resolver.find_conflicted_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].resolve(), conflicted_file.resolve())

    @patch('shared.conflict_resolver.GeminiAgent')
    async def test_resolve_file(self, mock_agent_class):
        # Setup mock agent
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Mock response from agent
        resolved_code = 'print("Hello Universe")'
        mock_agent.run_agent_session.return_value = (None, f"```python\n{resolved_code}\n```", None)

        # Create conflicted file
        conflicted_file = self.test_dir / "conflict.py"
        original_content = """
<<<<<<< HEAD
print("Hello World")
=======
print("Hello Universe")
>>>>>>> feature-branch
"""
        conflicted_file.write_text(original_content)

        # Run resolution
        result = await self.resolver.resolve_file(conflicted_file, agent_type="gemini")

        # Verify
        self.assertTrue(result["resolved"])
        self.assertEqual(result["resolved_content"], resolved_code)

        # Verify agent was called with correct prompt
        mock_agent.run_agent_session.assert_called_once()
        call_args = mock_agent.run_agent_session.call_args[0][0]
        self.assertIn("conflict.py", call_args)
        self.assertIn("<<<<<<< HEAD", call_args)

    def test_apply_resolution(self):
        target_file = self.test_dir / "target.py"
        target_file.write_text("Original")

        new_content = "Resolved"
        self.resolver.apply_resolution(target_file, new_content)

        self.assertEqual(target_file.read_text(), new_content)


if __name__ == '__main__':
    unittest.main()
