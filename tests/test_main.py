import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import shutil
import os
from pathlib import Path
from main import parse_args, main
import io


class TestMain(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_main_")
        self.project_dir = Path(self.tmp_dir)
        self.spec_file = self.project_dir / "spec.txt"
        self.spec_file.write_text("Spec content")

        # Patch argcomplete globally for all tests to avoid FD usage and verify behavior
        self.argcomplete_patcher = patch("main.argcomplete", MagicMock())
        self.mock_argcomplete = self.argcomplete_patcher.start()

    def tearDown(self):
        self.argcomplete_patcher.stop()
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_parse_args(self):
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            parse_args()
            mock_parse.assert_called()

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
    @patch("main.load_config_from_file", return_value={})
    async def test_main_gemini_run(
        self,
        mock_load_config,
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
        args.dashboard_url = "http://test"
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.dind = False
        args.command = None
        args.login = False
        args.max_error_wait = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        args.no_stream = False

        mock_parse_args.return_value = args
        mock_gen_id.return_value = "gemini_agent_test_123"

        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # Spec file exists
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Spec content"):
                await main()

        mock_gemini.assert_called()
        mock_source_cursor.assert_not_called()
        mock_source_gemini.assert_not_called()

        mock_cursor.assert_not_called()
        mock_sprint.assert_not_called()
        mock_git_safe.assert_called()
        mock_setup_logger.assert_called()
        mock_client_cls.assert_called()

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_cursor_run(
        self,
        mock_load_config,
        mock_gen_id,
        mock_run_cursor,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        # Setup args
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
        args.dind = False
        args.command = None
        args.login = False
        args.max_error_wait = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        args.no_stream = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.max_agents = 2

        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Spec"):
                await main()

        mock_run_cursor.assert_called()

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_sprint_run(
        self,
        mock_load_config,
        mock_gen_id,
        mock_run_sprint,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.agent = "gemini"
        args.spec = self.spec_file
        args.dashboard_only = False
        args.sprint = True  # Enables Sprint Mode
        args.timeout = 600.0
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False
        args.dind = False
        args.command = None
        args.login = False
        args.max_error_wait = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        args.no_stream = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.max_agents = 2

        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # I will patch Config to ensure sprint_mode is True for this test.
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            mock_conf.sprint_mode = True
            # FIX: Set project_dir to avoid garbage file creation
            mock_conf.project_dir = self.project_dir
            mock_config_cls.return_value = mock_conf

            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec"):
                    await main()

            mock_run_sprint.assert_called()

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_missing_spec_exit(self, mock_load_config, mock_gen, mock_logger, mock_parse_args):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.spec = None  # Missing spec
        args.dashboard_only = False
        args.jira_ticket = None
        args.jira_label = None
        args.dry_run = False # FIX: Ensure dry_run is False to avoid early exit
        args.command = None
        mock_parse_args.return_value = args

        # FIX: Configure mock_logger to return a tuple
        mock_logger.return_value = (MagicMock(), MagicMock())

        # feature_list_path.exists() -> False (fresh)
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            # FIX: Set project_dir to avoid garbage file creation (if any)
            mock_conf.project_dir = self.project_dir
            # FIX: Ensure jira_spec_content is None/False to fail the check
            mock_conf.jira_spec_content = None
            mock_config_cls.return_value = mock_conf

            with patch.object(
                Path, "exists", return_value=False
            ):  # No default spec either
                with self.assertRaises(SystemExit) as cm:
                    await main()
                self.assertEqual(cm.exception.code, 1)

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_cleanup(
        self,
        mock_load_config,
        mock_gen_id,
        mock_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
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
        args.dry_run = False # FIX
        args.dind = False
        args.command = None
        args.login = False
        args.max_error_wait = None
        args.no_dashboard = False
        args.dashboard_url = "http://localhost:7654"
        args.no_stream = False
        args.model = None
        args.max_iterations = None
        args.verbose = False
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.max_agents = 2

        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = True  # Not fresh
            mock_conf.sprint_mode = False
            # FIX: Set project_dir to avoid garbage file creation
            mock_conf.project_dir = self.project_dir

            # Mock PROJECT_SIGNED_OFF check
            # Create the file in temp dir to make exists() return True naturally
            (self.project_dir / "PROJECT_SIGNED_OFF").touch()

            mock_config_cls.return_value = mock_conf

            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec"):
                    await main()

            # mock_cleaner.assert_called() - Obsolete as it's now handled in the agent loop

    @patch("main.parse_args")
    @patch("shared.config_loader.ensure_config_exists")
    @patch("shared.config_loader.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    async def test_main_show_config_command(self, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config, mock_parse_args):
        args = MagicMock()
        args.command = "show-config"
        args.dry_run = False
        args.profile = None
        args.project_dir = self.project_dir
        args.agent = 'gemini'
        args.model = None
        args.max_iterations = None
        args.spec = self.spec_file
        args.verbose = False
        args.no_stream = True
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.timeout = None
        args.max_error_wait = None
        args.sprint = False
        args.max_agents = 1
        args.jira_ticket = None
        args.jira_label = None
        args.dind = False
        args.no_dashboard = True
        args.dashboard_url = None

        mock_parse_args.return_value = args
        mock_load_config.return_value = {}

        with self.assertRaises(SystemExit) as cm:
            await main()

        self.assertEqual(cm.exception.code, 0)
        mock_json_dumps.assert_called_once()

    @patch("main.parse_args")
    @patch("shared.config_loader.ensure_config_exists")
    @patch("shared.config_loader.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    @patch("sys.stderr")
    async def test_main_dry_run_deprecation(self, mock_stderr, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config, mock_parse_args):
        args = MagicMock()
        args.command = None
        args.dry_run = True
        args.profile = None
        args.project_dir = self.project_dir
        args.agent = 'gemini'
        args.model = None
        args.max_iterations = None
        args.spec = self.spec_file
        args.verbose = False
        args.no_stream = True
        args.verify_creation = False
        args.manager_frequency = 10
        args.manager_model = None
        args.manager_first = False
        args.login = False
        args.timeout = None
        args.max_error_wait = None
        args.sprint = False
        args.max_agents = 1
        args.jira_ticket = None
        args.jira_label = None
        args.dind = False
        args.no_dashboard = True
        args.dashboard_url = None

        mock_parse_args.return_value = args
        mock_load_config.return_value = {}

        with self.assertRaises(SystemExit) as cm:
            await main()

        self.assertEqual(cm.exception.code, 0)
        mock_json_dumps.assert_called_once()
        self.assertTrue(any("Warning: --dry-run is deprecated" in call.args[0] for call in mock_stderr.write.call_args_list))

    @patch('main.run_clean')
    @patch('sys.argv', ['main.py', 'clean', '--list'])
    async def test_main_clean_list_command(self, mock_run_clean):
        # This test ensures that when 'clean --list' is invoked, the run_clean function is called.
        # The actual logic of run_clean is tested in a dedicated test below.
        try:
            await main()
        except SystemExit:
            pass  # Expected exit
        mock_run_clean.assert_called_once()

    def test_run_clean_list_functionality(self):
        # Create dummy artifacts
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "feature_list.json").touch()

        args = MagicMock()
        args.project_dir = self.project_dir
        args.force = False
        args.archive = False
        args.list = True
        args.yes = True

        # Capture output
        from main import run_clean
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                run_clean(args)

        self.assertEqual(cm.exception.code, 0)

        output = f.getvalue()
        self.assertIn("COMPLETED", output)
        self.assertIn("feature_list.json", output)
        self.assertIn("would be cleaned", output)

        # Verify files were not deleted
        self.assertTrue((self.project_dir / "COMPLETED").exists())
        self.assertTrue((self.project_dir / "feature_list.json").exists())

    @patch('main.parse_args')
    async def test_main_completion_command(self, mock_parse_args):
        args = MagicMock()
        args.command = "completion"
        mock_parse_args.return_value = args

        # Set return value for the global mock
        self.mock_argcomplete.shellcode.return_value = "completion_script"

        # Capture stdout
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                await main()

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()
        self.assertIn("completion_script", output)


if __name__ == "__main__":
    unittest.main()
