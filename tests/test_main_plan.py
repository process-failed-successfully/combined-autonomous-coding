
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import argparse
from pathlib import Path
import json
import asyncio

from main import run_plan
from agents.gemini.agent import GeminiAgent


class TestMainPlan(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("test_project_plan")
        self.project_dir.mkdir(exist_ok=True)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("A simple calculator app")
        self.feature_file = self.project_dir / "feature_list.json"
        if self.feature_file.exists():
            self.feature_file.unlink()

    def tearDown(self):
        if self.spec_file.exists():
            self.spec_file.unlink()
        if self.feature_file.exists():
            self.feature_file.unlink()
        if self.project_dir.exists():
            self.project_dir.rmdir()

    @patch('main.setup_logger')
    @patch('main.ensure_config_exists')
    @patch('main.load_config_from_file')
    def test_run_plan_no_spec_file(self, mock_load_config, mock_ensure_config, mock_setup_logger):
        # Arrange
        mock_load_config.return_value = {}
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        args = argparse.Namespace(
            spec=None,  # No spec file
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            verbose=False,
            profile=None,
            command="plan"
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            asyncio.run(run_plan(args))

        self.assertEqual(cm.exception.code, 1)

    @patch('main.GeminiAgent')
    @patch('main.CursorAgent')
    @patch('main.LocalAgent')
    @patch('main.OpenRouterAgent')
    @patch('main.setup_logger')
    @patch('main.ensure_config_exists')
    @patch('main.load_config_from_file')
    def test_run_plan_success(self, mock_load_config, mock_ensure_config, mock_setup_logger, mock_oa, mock_la, mock_ca, mock_ga):
        # Arrange
        mock_load_config.return_value = {}
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # Mock agent instance and its planning method
        mock_agent_instance = MagicMock(spec=GeminiAgent)
        mock_agent_instance.run_planning_session = AsyncMock(return_value=True)

        # When the GeminiAgent class is instantiated, return our mock instance
        mock_ga.return_value = mock_agent_instance

        # Simulate the feature file being created by the planning session
        def side_effect(*args, **kwargs):
            self.feature_file.write_text(json.dumps([{"feature": "Addition"}]))
            return asyncio.sleep(0)

        mock_agent_instance.run_planning_session.side_effect = side_effect

        args = argparse.Namespace(
            spec=self.spec_file,
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            verbose=False,
            profile=None,
            command="plan"
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            asyncio.run(run_plan(args))

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_ga.assert_called_once()
        mock_agent_instance.run_planning_session.assert_awaited_once()
        self.assertTrue(self.feature_file.exists())
        with open(self.feature_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data, [{"feature": "Addition"}])


if __name__ == '__main__':
    unittest.main()
