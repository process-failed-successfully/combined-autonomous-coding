import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path
from main import parse_args, main


class TestMain(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_main_")
        self.project_dir = Path(self.tmp_dir)
        self.spec_file = self.project_dir / "spec.txt"
        self.spec_file.write_text("Spec content")

        self.config_file = self.project_dir / "agent_config.yaml"
        self.config_file.write_text("model: test-model")

        patcher = patch('shared.config_loader.get_config_path', return_value=self.config_file)
        self.mock_get_config_path = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def create_base_mock_args(self):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "gemini"
        args.model = None
        args.max_iterations = None
        args.spec = self.spec_file
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.sprint = False
        args.max_agents = 2
        args.timeout = None
        args.max_error_wait = None
        args.dashboard_url = "http://test"
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.dind = False
        args.no_dashboard = False
        return args

    def test_parse_args(self):
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            parse_args()
            mock_parse.assert_called()

    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_gemini_run(
        self, mock_init_db, mock_gen_id, mock_client_cls, mock_git_safe,
        mock_setup_logger, mock_parse_args, mock_run_gemini, mock_run_cursor,
        mock_run_sprint
    ):
        args = self.create_base_mock_args()
        args.agent = "gemini"
        mock_parse_args.return_value = args

        mock_gen_id.return_value = "gemini_agent_test_123"
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        await main()

        mock_run_gemini.assert_called()
        mock_run_cursor.assert_not_called()
        mock_run_sprint.assert_not_called()

    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_cursor_run(
        self, mock_init_db, mock_gen_id, mock_client_cls, mock_git_safe,
        mock_setup_logger, mock_parse_args, mock_run_gemini, mock_run_cursor,
        mock_run_sprint
    ):
        args = self.create_base_mock_args()
        args.agent = "cursor"
        mock_parse_args.return_value = args

        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        await main()

        mock_run_cursor.assert_called()
        mock_run_gemini.assert_not_called()
        mock_run_sprint.assert_not_called()

    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_sprint_run(
        self, mock_init_db, mock_gen_id, mock_client_cls, mock_git_safe,
        mock_setup_logger, mock_parse_args, mock_run_gemini, mock_run_cursor,
        mock_run_sprint
    ):
        args = self.create_base_mock_args()
        args.sprint = True
        mock_parse_args.return_value = args

        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        await main()

        mock_run_sprint.assert_called()
        mock_run_gemini.assert_not_called()
        mock_run_cursor.assert_not_called()

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_missing_spec_exit(self, mock_db, mock_gen, mock_logger, mock_parse_args):
        args = self.create_base_mock_args()
        args.spec = None
        args.jira_ticket = None
        args.jira_label = None
        mock_parse_args.return_value = args

        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(SystemExit) as cm:
                await main()
            self.assertEqual(cm.exception.code, 1)

    @patch("main.parse_args")
    @patch("sys.exit")
    @patch("builtins.print")
    async def test_main_dry_run(self, mock_print, mock_exit, mock_parse_args):
        args = self.create_base_mock_args()
        args.dry_run = True
        args.model = "test-model-dry-run"
        args.max_iterations = 50
        args.verbose = True

        mock_parse_args.return_value = args

        await main()

        mock_exit.assert_called_once_with(0)
        mock_print.assert_called_once()

        import json
        output = mock_print.call_args[0][0]
        config_data = json.loads(output)

        self.assertEqual(config_data['model'], 'test-model-dry-run')
        self.assertEqual(config_data['max_iterations'], 50)
        self.assertTrue(config_data['verbose'])
        self.assertEqual(config_data['project_dir'], str(self.project_dir))


if __name__ == "__main__":
    unittest.main()
