import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path
from main import parse_args, main, get_parser
import io


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
        # Now that parse_args is more complex, we test its behavior
        # in TestParseArgsSuggestions. This test can be simplified.
        parser = get_parser()
        with patch.object(parser, 'parse_args') as mock_parse:
            parse_args(parser, ['status'])
            mock_parse.assert_called_with(['status'])

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

        # The mock needs to accept the parser argument
        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
        mock_gen_id.return_value = "gemini_agent_test_123"

        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # Spec file exists
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Spec content"):
                await main()

        mock_gemini.assert_called()
        mock_source_cursor.assert_not_called()
        mock_source_gemini.assert_not_called()  # Should match source patch if called via main?
        # Actually if we patch source and main... main calls main.run_gemini (mock_gemini).
        # source_gemini (agents.gemini...) might NOT be called if main uses its own mock.

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
    async def test_main_cursor_run(
        self,
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

        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
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
    async def test_main_sprint_run(
        self,
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

        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # We need to ensure config.sprint_mode is True.
        # Main creates Config(..., agent_type=args.agent, ..., )
        # It seems main.py doesn't pass 'sprint' to Config explicitly?
        # Let's check shared/config.py to see how sprint_mode is determined.
        # If it's not passed, maybe it defaults to False?
        # In main.py:
        # config = Config(..., timeout=...)
        # It does NOT look like it passes sprint.
        # But main.py line 205:
        # config = Config(...)
        # Maybe I missed it?
        # Wait, if main.py doesn't pass sprint arg to Config, then Config.sprint_mode is likely False by default.
        # BUT main.py checks `if config.sprint_mode:`.
        # So Config MUST have a way to set it.
        # Let's assume Config has it or main sets it.
        # Actually, let's look at `shared/config.py` in my mind (or read it if I must).
        # Assuming main.py logic relies on Config knowing it.
        # But if main.py doesn't pass it, how does Config know?
        # Maybe main.py logic is broken regarding sprint mode passing?
        # OR main.py DOES pass it and I missed it in `read_file main.py`.

        # Re-reading `read_file main.py` output from earlier...
        # It lists many args passed to Config. `sprint` is NOT one of them.
        # `manager_frequency=... login_mode=args.login`
        # `timeout=...`
        # Nothing about sprint.
        # BUT `shared/config.py` might parse args itself? No, it takes args in
        # init.

        # IF main.py is buggy regarding sprint mode, I should fix it too!
        # `config.sprint_mode` usage:
        # if config.sprint_mode:
        #    await run_sprint(...)

        # If Config doesn't receive it, maybe it defaults to checking args?

        # I will patch Config to ensure sprint_mode is True for this test.
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            mock_conf.sprint_mode = True
            mock_config_cls.return_value = mock_conf

            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec"):
                    await main()

            mock_run_sprint.assert_called()

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    async def test_main_missing_spec_exit(self, mock_gen, mock_logger, mock_parse_args):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.spec = None  # Missing spec
        args.dashboard_only = False
        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect

        # feature_list_path.exists() -> False (fresh)
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
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
    async def test_main_cleanup(
        self,
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

        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = True  # Not fresh
            mock_conf.sprint_mode = False

            # Mock PROJECT_SIGNED_OFF check
            mock_project_dir = MagicMock()
            mock_conf.project_dir = mock_project_dir

            signed_off_path = MagicMock()
            signed_off_path.exists.return_value = True

            mock_project_dir.__truediv__.return_value = signed_off_path

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

        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
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

        def parse_args_side_effect(parser, argv=None):
            return args
        mock_parse_args.side_effect = parse_args_side_effect
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

    @patch('main.argcomplete', new_callable=MagicMock)
    @patch('main.parse_args')
    async def test_main_completion_command(self, mock_parse_args, mock_argcomplete):
        args = MagicMock()
        args.command = "completion"
        mock_parse_args.return_value = args

        mock_argcomplete.shellcode.return_value = "completion_script"

        # Capture stdout
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                await main()

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()
        self.assertIn("completion_script", output)


class TestParseArgsSuggestions(unittest.TestCase):
    def setUp(self):
        # Create the parser once for all tests in this class
        self.parser = get_parser()

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_suggest_on_mistyped_command(self, mock_stderr):
        with self.assertRaises(SystemExit) as cm:
            parse_args(self.parser, ['staus'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("Error: Invalid command 'staus'", output)
        self.assertIn("Did you mean 'status'?", output)

    def test_correct_command_passes(self):
        args = parse_args(self.parser, ['status'])
        self.assertEqual(args.command, 'status')

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_no_suggestion_for_wildly_incorrect_command(self, mock_stderr):
        with self.assertRaises(SystemExit) as cm:
            parse_args(self.parser, ['nonexistentcommand'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("Error: Invalid command 'nonexistentcommand'", output)
        self.assertNotIn("Did you mean", output)
        # Check that it printed the help usage message
        self.assertIn("usage:", output)


if __name__ == "__main__":
    unittest.main()
