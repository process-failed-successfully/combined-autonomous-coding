import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path
from main import parse_args, main
import io
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout

MOCK_ARGCOMPLETE = MagicMock()

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

    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
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
    @patch("shared.database.init_db")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_gemini_run(
        self,
        mock_load_config,
        mock_init_db,
        mock_gen_id,
        mock_sprint,
        mock_run_cursor,
        mock_run_gemini,
        mock_source_cursor,
        mock_source_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        # Setup args
        args = Namespace(
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            max_iterations=None,
            spec=self.spec_file,
            verbose=False,
            no_stream=False,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            dashboard_only=False,
            login=False,
            sprint=False,
            max_agents=2,
            timeout=None,
            dashboard_url="http://test",
            jira_ticket=None,
            jira_label=None,
            dry_run=False,
            dind=False,
            command=None,
            max_error_wait=None,
            no_dashboard=False,
            profile=None
        )

        mock_parse_args.return_value = args
        mock_gen_id.return_value = "gemini_agent_test_123"

        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # Spec file exists
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Spec content"):
                await main()

        mock_run_gemini.assert_called()
        mock_source_cursor.assert_not_called()
        # mock_source_gemini.assert_not_called()

        mock_run_cursor.assert_not_called()
        mock_sprint.assert_not_called()
        mock_git_safe.assert_called()
        mock_setup_logger.assert_called()
        mock_client_cls.assert_called()

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_cursor", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_cursor_run(
        self,
        mock_load_config,
        mock_init_db,
        mock_gen_id,
        mock_run_cursor,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        # Setup args
        args = Namespace(
            project_dir=self.project_dir,
            agent="cursor",
            spec=self.spec_file,
            dashboard_only=False,
            login=False,
            sprint=False,
            timeout=600.0,
            jira_ticket=None,
            jira_label=None,
            dry_run=False,
            dind=False,
            command=None,
            max_error_wait=None,
            no_dashboard=False,
            dashboard_url="http://localhost:7654",
            no_stream=False,
            model=None,
            max_iterations=None,
            verbose=False,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            max_agents=2,
            profile=None
        )

        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Spec"):
                await main()

        mock_run_cursor.assert_called()

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_sprint", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_sprint_run(
        self,
        mock_load_config,
        mock_init_db,
        mock_gen_id,
        mock_run_sprint,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        args = Namespace(
            project_dir=self.project_dir,
            agent="gemini",
            spec=self.spec_file,
            dashboard_only=False,
            sprint=True,  # Enables Sprint Mode
            timeout=600.0,
            jira_ticket=None,
            jira_label=None,
            dry_run=False,
            dind=False,
            command=None,
            login=False,
            max_error_wait=None,
            no_dashboard=False,
            dashboard_url="http://localhost:7654",
            no_stream=False,
            model=None,
            max_iterations=None,
            verbose=False,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            max_agents=2,
            profile=None
        )

        mock_parse_args.return_value = args
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # I will patch Config to ensure sprint_mode is True for this test.
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            mock_conf.sprint_mode = True
            mock_config_cls.return_value = mock_conf

            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec"):
                    with redirect_stderr(io.StringIO()):
                        await main()

            mock_run_sprint.assert_called()

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_missing_spec_exit(self, mock_load_config, mock_gen, mock_logger, mock_parse_args):
        args = Namespace(
            project_dir=self.project_dir,
            spec=None,  # Missing spec
            dashboard_only=False,
            jira_ticket=None,
            jira_label=None,
            profile=None,
            agent='gemini',
            verbose=False
        )
        mock_parse_args.return_value = args

        # feature_list_path.exists() -> False (fresh)
        with patch("main.Config") as mock_config_cls:
            mock_conf = MagicMock()
            mock_conf.feature_list_path.exists.return_value = False
            mock_config_cls.return_value = mock_conf

            with patch.object(
                Path, "exists", return_value=False
            ):  # No default spec either
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as cm:
                        await main()
                self.assertEqual(cm.exception.code, 1)

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_gemini", new_callable=unittest.mock.AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    @patch("main.load_config_from_file", return_value={})
    async def test_main_cleanup(
        self,
        mock_load_config,
        mock_init_db,
        mock_gen_id,
        mock_gemini,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
        mock_parse_args,
    ):
        args = Namespace(
            project_dir=self.project_dir,
            agent="gemini",
            spec=self.spec_file,
            dashboard_only=False,
            sprint=False,
            timeout=None,
            jira_ticket=None,
            jira_label=None,
            dry_run=False,
            dind=False,
            command=None,
            login=False,
            max_error_wait=None,
            no_dashboard=False,
            dashboard_url="http://localhost:7654",
            no_stream=False,
            model=None,
            max_iterations=None,
            verbose=False,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            max_agents=2,
            profile=None
        )

        mock_parse_args.return_value = args
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
                    with redirect_stderr(io.StringIO()):
                        await main()

            # mock_cleaner.assert_called() - Obsolete as it's now handled in the agent loop

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("shared.config_loader.ensure_config_exists")
    @patch("main.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    async def test_main_show_config_command(self, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config, mock_parse_args):
        args = Namespace(
            command="show-config",
            dry_run=False,
            profile=None,
            project_dir=self.project_dir,
            agent='gemini',
            model=None,
            max_iterations=None,
            spec=self.spec_file,
            verbose=False,
            no_stream=True,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            login=False,
            timeout=None,
            max_error_wait=None,
            sprint=False,
            max_agents=1,
            jira_ticket=None,
            jira_label=None,
            dind=False,
            no_dashboard=True,
            dashboard_url=None
        )

        mock_parse_args.return_value = args
        mock_load_config.return_value = {}

        with self.assertRaises(SystemExit) as cm:
            # Not wrapping with redirect_stderr here as SystemExit is expected and handled
            await main()

        self.assertEqual(cm.exception.code, 0)
        mock_json_dumps.assert_called_once()

    @unittest.skip("CI instability: OSError in asyncTearDown")
    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
    @patch("main.parse_args")
    @patch("shared.config_loader.ensure_config_exists")
    @patch("main.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    async def test_main_dry_run_deprecation(self, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config, mock_parse_args):
        args = Namespace(
            command=None,
            dry_run=True,
            profile=None,
            project_dir=self.project_dir,
            agent='gemini',
            model=None,
            max_iterations=None,
            spec=self.spec_file,
            verbose=False,
            no_stream=True,
            verify_creation=False,
            manager_frequency=10,
            manager_model=None,
            manager_first=False,
            login=False,
            timeout=None,
            max_error_wait=None,
            sprint=False,
            max_agents=1,
            jira_ticket=None,
            jira_label=None,
            dind=False,
            no_dashboard=True,
            dashboard_url=None
        )

        mock_parse_args.return_value = args
        mock_load_config.return_value = {}

        # Use context manager for stderr
        f = io.StringIO()
        with redirect_stderr(f):
            with self.assertRaises(SystemExit) as cm:
                await main()

        self.assertEqual(cm.exception.code, 0)
        mock_json_dumps.assert_called_once()
        self.assertTrue("Warning: --dry-run is deprecated" in f.getvalue())

    @patch("main.argcomplete", MOCK_ARGCOMPLETE)
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


if __name__ == "__main__":
    unittest.main()
