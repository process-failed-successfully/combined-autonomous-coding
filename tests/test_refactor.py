import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
from shared.refactor import RefactorManager


class TestRefactorManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.target_file = self.project_dir / "target.py"
        self.target_file.write_text("def foo():\n    print('hello')\n")
        self.manager = RefactorManager(self.project_dir)

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("shared.refactor.GeminiAgent")
    async def test_refactor_file_success(self, MockAgent):
        # Setup Mock
        mock_agent_instance = MockAgent.return_value
        # Mock run_agent_session to return (None, response, None)
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(
            None,
            "Here is the code:\n```python\ndef foo():\n    print('world')\n```",
            None
        ))

        result = await self.manager.refactor_file(
            self.target_file,
            "Change hello to world"
        )

        self.assertTrue(result["changed"])
        self.assertIn("print('world')", result["new_content"])
        self.assertIn("-    print('hello')", result["diff"])
        self.assertIn("+    print('world')", result["diff"])

    @patch("shared.refactor.GeminiAgent")
    async def test_refactor_file_no_change(self, MockAgent):
        mock_agent_instance = MockAgent.return_value
        # Return same content
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(
            None,
            "```python\ndef foo():\n    print('hello')\n```",
            None
        ))

        result = await self.manager.refactor_file(
            self.target_file,
            "Do nothing"
        )

        self.assertFalse(result["changed"])
        self.assertEqual(result["new_content"].strip(), result["original_content"].strip())

    @patch("shared.refactor.GeminiAgent")
    async def test_refactor_file_no_code_block(self, MockAgent):
        # Test fallback when agent doesn't use markdown blocks but returns code
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(
            None,
            "def foo():\n    print('fallback')",
            None
        ))

        result = await self.manager.refactor_file(
            self.target_file,
            "Change to fallback"
        )

        self.assertTrue(result["changed"])
        self.assertIn("print('fallback')", result["new_content"])

    def test_apply_changes(self):
        new_content = "def foo():\n    print('applied')\n"
        self.manager.apply_changes(self.target_file, new_content)
        self.assertEqual(self.target_file.read_text(), new_content)


if __name__ == "__main__":
    unittest.main()
