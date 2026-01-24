import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import io
from typing import cast

from shared.recipe_learner import LogParser, RecipeLearner

class TestLogParser(unittest.TestCase):
    def test_parse(self):
        log_content = """2023-10-27 10:00:00 - INFO - [Executing Bash] ls -la
2023-10-27 10:00:01 - INFO - Some output
2023-10-27 10:00:02 - INFO - [Executing Bash] pytest
"""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = log_content

        parser = LogParser()
        commands = parser.parse(mock_path)
        self.assertEqual(commands, ["ls -la", "pytest"])

    def test_parse_no_file(self):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        parser = LogParser()
        commands = parser.parse(mock_path)
        self.assertEqual(commands, [])

class TestRecipeLearner(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.learner = RecipeLearner(self.project_dir)
        self.learner.recipe_manager = MagicMock()

    @patch('shared.recipe_learner.get_latest_log_file')
    @patch('shared.recipe_learner.LogParser')
    @patch('shared.recipe_learner.run_ask_logic', new_callable=AsyncMock)
    async def test_learn_from_run_success(self, mock_ask, mock_parser_cls, mock_get_log):
        # Setup mocks
        mock_log_file = MagicMock()
        mock_log_file.exists.return_value = True
        mock_get_log.return_value = mock_log_file

        mock_parser = mock_parser_cls.return_value
        mock_parser.parse.return_value = ["ls", "echo 'hello'"]

        # Mock ask logic to print JSON response
        async def side_effect(*args, **kwargs):
            print('["ls", "echo hello"]')
            return True

        mock_ask.side_effect = side_effect

        # Run
        # Redirect stdout/stderr to suppress prints during test
        with patch('sys.stdout', new=io.StringIO()):
            result = await self.learner.learn_from_run(None, "test_recipe")

        # Verify
        self.assertTrue(result)

        # Cast to MagicMock to satisfy Mypy
        manager_mock = cast(MagicMock, self.learner.recipe_manager)
        manager_mock.add_recipe.assert_called_with("test_recipe", ["ls", "echo hello"])

    @patch('shared.recipe_learner.get_latest_log_file')
    async def test_learn_no_log(self, mock_get_log):
        mock_get_log.return_value = None
        with patch('sys.stdout', new=io.StringIO()):
            result = await self.learner.learn_from_run(None, "test_recipe")
        self.assertFalse(result)

    @patch('shared.recipe_learner.get_latest_log_file')
    @patch('shared.recipe_learner.LogParser')
    @patch('shared.recipe_learner.run_ask_logic', new_callable=AsyncMock)
    async def test_learn_fail_parsing(self, mock_ask, mock_parser_cls, mock_get_log):
        # Setup mocks
        mock_log_file = MagicMock()
        mock_log_file.exists.return_value = True
        mock_get_log.return_value = mock_log_file

        mock_parser = mock_parser_cls.return_value
        mock_parser.parse.return_value = ["ls"]

        # Mock ask logic to return invalid JSON
        async def side_effect(*args, **kwargs):
            print('Not JSON')
            return True

        mock_ask.side_effect = side_effect

        with patch('sys.stdout', new=io.StringIO()):
            result = await self.learner.learn_from_run(None, "test_recipe")

        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
