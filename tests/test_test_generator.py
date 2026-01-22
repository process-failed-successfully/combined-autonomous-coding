import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.test_generator import TestGenerator


class TestTestGenerator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.generator = TestGenerator(self.project_dir)

    @patch("shared.test_generator.GeminiAgent")
    async def test_generate_tests_success(self, MockAgent):
        # Setup mock agent
        mock_agent_instance = MockAgent.return_value
        # Mock run_agent_session to return a code block
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("", "```python\ndef test_something(): pass\n```", ""))

        # Setup target file
        target_file = MagicMock(spec=Path)
        target_file.exists.return_value = True
        target_file.resolve.return_value = target_file
        target_file.read_text.return_value = "def something(): pass"
        target_file.stem = "something"
        target_file.name = "something.py"
        target_file.relative_to.return_value = Path("something.py")

        # Setup output file
        output_file = MagicMock(spec=Path)
        output_file.resolve.return_value = output_file
        output_file.relative_to.return_value = Path("tests/test_something.py")
        output_file.parent.mkdir = MagicMock()

        # Execute
        result = await self.generator.generate_tests(
            target_file=target_file,
            output_file=output_file,
            agent_type="gemini"
        )

        # Verify
        self.assertTrue(result)
        # Check if agent was called
        mock_agent_instance.run_agent_session.assert_called_once()
        # Check if file was written
        output_file.write_text.assert_called_once_with("def test_something(): pass", encoding="utf-8")

    @patch("shared.test_generator.GeminiAgent")
    async def test_generate_tests_no_code_block(self, MockAgent):
        # Setup mock agent to return raw code without markdown
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("", "def test_something(): pass", ""))

        target_file = MagicMock(spec=Path)
        target_file.exists.return_value = True
        target_file.resolve.return_value = target_file
        target_file.read_text.return_value = "def something(): pass"
        target_file.stem = "something"
        target_file.name = "something.py"
        target_file.relative_to.return_value = Path("something.py")

        output_file = MagicMock(spec=Path)
        output_file.resolve.return_value = output_file
        output_file.parent.mkdir = MagicMock()

        result = await self.generator.generate_tests(
            target_file=target_file,
            output_file=output_file,
            agent_type="gemini"
        )

        self.assertTrue(result)
        output_file.write_text.assert_called_once_with("def test_something(): pass", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
