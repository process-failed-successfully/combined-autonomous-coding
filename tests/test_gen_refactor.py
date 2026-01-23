import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from shared.test_generator import TestGenerator


class TestTestGenerator(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.project_dir = Path("test_project_gen")
        self.project_dir.mkdir(exist_ok=True)
        self.target_file = self.project_dir / "math.py"
        self.target_file.write_text("def add(a, b): return a + b")

    def tearDown(self):
        if self.target_file.exists():
            self.target_file.unlink()
        if self.project_dir.exists():
            import shutil
            shutil.rmtree(self.project_dir)

    @patch('shared.test_generator.GeminiAgent')
    async def test_generate_test_code_success(self, mock_agent_class):
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        expected_code = "def test_add(): assert add(1, 1) == 2"
        mock_response = f"```python\n{expected_code}\n```"

        mock_agent_instance.run_agent_session = AsyncMock(return_value=(None, mock_response, None))

        generator = TestGenerator(self.project_dir)

        # Act
        success, code = await generator.generate_test_code(self.target_file)

        # Assert
        self.assertTrue(success)
        self.assertEqual(code, expected_code)
        mock_agent_instance.run_agent_session.assert_awaited_once()

    @patch('shared.test_generator.GeminiAgent')
    async def test_generate_test_code_failure(self, mock_agent_class):
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        mock_agent_instance.run_agent_session.side_effect = Exception("API Error")

        generator = TestGenerator(self.project_dir)

        # Act
        success, code = await generator.generate_test_code(self.target_file)

        # Assert
        self.assertFalse(success)
        self.assertIn("API Error", code)


if __name__ == '__main__':
    unittest.main()
