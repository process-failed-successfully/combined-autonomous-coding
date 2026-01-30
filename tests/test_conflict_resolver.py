
import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from shared.conflict_resolver import ConflictResolver, Conflict
from shared.config import Config

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

    def test_parse_conflicts(self):
        content = """Before
<<<<<<< HEAD
Our Change
=======
Their Change
>>>>>>> feature
After
<<<<<<< HEAD
Conflict 2 Ours
||||||| base
Base Content
=======
Conflict 2 Theirs
>>>>>>> feature
End
"""
        conflicts = self.resolver.parse_conflicts(content)
        self.assertEqual(len(conflicts), 2)

        # Conflict 1
        c1 = conflicts[0]
        self.assertEqual(c1.start_line, 1)
        self.assertEqual(c1.sep_line, 3)
        self.assertEqual(c1.end_line, 5)
        self.assertEqual(c1.ours_content, "Our Change\n")
        self.assertEqual(c1.theirs_content, "Their Change\n")
        self.assertIsNone(c1.base_content)

        # Conflict 2 (diff3)
        c2 = conflicts[1]
        self.assertEqual(c2.start_line, 7)
        self.assertEqual(c2.base_line, 9)
        self.assertEqual(c2.sep_line, 11)
        self.assertEqual(c2.end_line, 13)
        self.assertEqual(c2.ours_content, "Conflict 2 Ours\n")
        self.assertEqual(c2.base_content, "Base Content\n")
        self.assertEqual(c2.theirs_content, "Conflict 2 Theirs\n")

    def test_resolve_manual(self):
        file_path = self.test_dir / "manual_conflict.txt"
        file_path.write_text("""Start
<<<<<<< HEAD
Ours
=======
Theirs
>>>>>>> feature
End""")

        # Test Resolve Ours
        self.resolver.resolve_manual(file_path, 0, "ours")
        expected_ours = """Start
Ours
End"""
        self.assertEqual(file_path.read_text(), expected_ours)

        # Reset and Test Resolve Theirs
        file_path.write_text("""Start
<<<<<<< HEAD
Ours
=======
Theirs
>>>>>>> feature
End""")
        self.resolver.resolve_manual(file_path, 0, "theirs")
        expected_theirs = """Start
Theirs
End"""
        self.assertEqual(file_path.read_text(), expected_theirs)

    def test_resolve_all_manual(self):
        file_path = self.test_dir / "multi_conflict.txt"
        file_path.write_text("""
<<<<<<< HEAD
A
=======
B
>>>>>>> f1
Middle
<<<<<<< HEAD
C
=======
D
>>>>>>> f1
""")

        count = self.resolver.resolve_all_manual(file_path, "theirs")
        self.assertEqual(count, 2)
        self.assertEqual(file_path.read_text(), "\nB\nMiddle\nD\n")

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
