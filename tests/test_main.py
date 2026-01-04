import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
import json
from io import StringIO
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from main import parse_args, main


class TestMain(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_main_")
        self.project_dir = Path(self.tmp_dir)
        self.spec_file = self.project_dir / "spec.txt"
        self.spec_file.write_text("Spec content")

    def tearDown(self):
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_parse_args(self):
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            parse_args()
            mock_parse.assert_called()

    @patch("shared.config_loader.load_config_from_file", return_value={})
    @patch("shared.config_loader.ensure_config_exists", return_value=None)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("agents.gemini.run_autonomous_agent", new_callable=unittest.mock.AsyncMock)
    @patch("agents.cursor.run_autonomous_agent", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    async def test_main_gemini_run(
        self,
        mock_gen_id,
        mock_sprint,
        mock_cursor,
        mock_gemini,
        mock_source_cursor,
        mock_source_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
        mock_ensure_config,
        mock_load_config,
    ):
        # Setup args
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
        args.dashboard_only = False
        args.login = False
        args.sprint = False
        args.max_agents = 2
        args.timeout = None
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://test"
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        mock_parse_args.return_value = args
        mock_gen_id.return_value = "gemini_agent_test_123"
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        await main()
        mock_gemini.assert_called()
        mock_source_cursor.assert_not_called()
        mock_source_gemini.assert_not_called()
        mock_cursor.assert_not_called()
        mock_sprint.assert_not_called()
        mock_git_safe.assert_called()
        mock_setup_logger.assert_called()
        mock_client_cls.assert_called()

    @patch("shared.config_loader.load_config_from_file", return_value={})
    @patch("shared.config_loader.ensure_config_exists", return_value=None)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    async def test_main_cursor_run(
        self,
        mock_gen_id,
        mock_run_cursor,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
        mock_ensure_config,
        mock_load_config,
    ):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "cursor"
        args.spec = self.spec_file
        args.dashboard_only = False
        args.login = False
        args.sprint = False
        args.timeout = 600.0
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.max_agents = 1
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        await main()
        mock_run_cursor.assert_called()

    @patch("shared.config_loader.load_config_from_file", return_value={})
    @patch("shared.config_loader.ensure_config_exists", return_value=None)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    async def test_main_sprint_run(
        self,
        mock_gen_id,
        mock_run_sprint,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
        mock_ensure_config,
        mock_load_config,
    ):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "gemini"
        args.spec = self.spec_file
        args.dashboard_only = False
        args.sprint = True
        args.timeout = 600.0
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.max_agents = 1
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            mock_conf.sprint_mode = True
            mock_config_cls.return_value = mock_conf
            await main()
            mock_run_sprint.assert_called()

    @patch("main.parse_args")
    async def test_main_dashboard_only_exit(self, mock_parse_args):
        args = MagicMock()
        args.dashboard_only = True
        args.dry_run = False
        args.command = None
        mock_parse_args.return_value = args
        with self.assertRaises(SystemExit) as cm:
            await main()
        self.assertEqual(cm.exception.code, 1)

    @patch("shared.config_loader.get_config_path")
    @patch("main.parse_args")
    @patch("main.setup_logger")
    async def test_main_missing_spec_exit(
        self, mock_setup_logger, mock_parse_args, mock_get_config_path
    ):
        mock_get_config_path.return_value = self.project_dir / "agent_config.yaml"
        args = MagicMock()
        args.project_dir = self.project_dir
        args.spec = None
        args.dashboard_only = False
        args.dry_run = False
        args.jira_ticket = None
        args.jira_label = None
        args.agent = "gemini"
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.sprint = False
        args.max_agents = 1
        args.timeout = 600.0
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        with self.assertRaises(SystemExit) as cm:
            await main()
        self.assertEqual(cm.exception.code, 1)

    @patch("shared.config_loader.load_config_from_file", return_value={})
    @patch("shared.config_loader.ensure_config_exists", return_value=None)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    async def test_main_cleanup(
        self,
        mock_gen_id,
        mock_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
        mock_ensure_config,
        mock_load_config,
    ):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "gemini"
        args.spec = self.spec_file
        args.dashboard_only = False
        args.sprint = False
        args.timeout = None
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.max_agents = 1
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = True
            mock_conf.sprint_mode = False
            mock_project_dir = MagicMock()
            mock_conf.project_dir = mock_project_dir
            signed_off_path = MagicMock()
            signed_off_path.exists.return_value = True
            mock_project_dir.__truediv__.return_value = signed_off_path
            mock_config_cls.return_value = mock_conf
            await main()

    @patch("sys.stdout", new_callable=StringIO)
    @patch("shared.config_loader.load_config_from_file", return_value={})
    @patch("shared.config_loader.ensure_config_exists", return_value=None)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    async def test_main_dry_run(
        self,
        mock_gen_id,
        mock_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
        mock_ensure_config,
        mock_load_config,
        mock_stdout,
    ):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "gemini"
        args.spec = self.spec_file
        args.dry_run = True
        args.jira_ticket = None
        args.jira_label = None
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.no_stream = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.sprint = False
        args.max_agents = 1
        args.timeout = 600.0
        args.max_error_wait = 600.0
        args.dind = False
        args.command = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        with self.assertRaises(SystemExit) as cm:
            await main()
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertTrue(output.startswith("{"))
        data = json.loads(output)
        self.assertEqual(data["agent_type"], "gemini")
        self.assertEqual(data["project_dir"], str(self.project_dir))
        mock_gemini.assert_not_called()


if __name__ == "__main__":
    unittest.main()
