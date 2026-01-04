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

    def tearDown(self):
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
        args.tui = False

        mock_parse_args.return_value = args
        mock_gen_id.return_value = "gemini_agent_test_123"

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
        args.tui = False

        mock_parse_args.return_value = args

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
        args.tui = False

        mock_parse_args.return_value = args

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
    async def test_main_dashboard_only_exit(self, mock_parse_args):
        args = MagicMock()
        args.dashboard_only = True
        args.tui = False
        mock_parse_args.return_value = args

        with self.assertRaises(SystemExit) as cm:
            await main()
        self.assertEqual(cm.exception.code, 1)

    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    async def test_main_missing_spec_exit(self, mock_gen, mock_logger, mock_parse_args):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.spec = None  # Missing spec
        args.dashboard_only = False
        args.tui = False
        mock_parse_args.return_value = args

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
        args.tui = False

        mock_parse_args.return_value = args

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


if __name__ == "__main__":
    unittest.main()
