import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import shutil
import os
import sys
import io
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
        # We must mock sys.argv for parse_args to work in isolation if it relies on it,
        # but parse_args(argv) usually takes an argument.
        # main.py: parse_args(argv=None) -> uses sys.argv if None.
        with patch.object(sys, 'argv', ["main.py", "--help"]):
             with self.assertRaises(SystemExit):
                 parse_args()

    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("agents.gemini.run_autonomous_agent", new_callable=AsyncMock)
    @patch("agents.cursor.run_autonomous_agent", new_callable=AsyncMock)
    @patch("main.run_gemini", new_callable=AsyncMock)
    @patch("main.run_cursor", new_callable=AsyncMock)
    @patch("main.run_sprint", new_callable=AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_gemini_run(
        self,
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
    ):
        mock_gen_id.return_value = "gemini_agent_test_123"
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        # Use sys.argv patching
        cmd = ["main.py", "--project-dir", str(self.project_dir), "--agent", "gemini", "--spec", str(self.spec_file)]
        with patch.object(sys, 'argv', cmd):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec content"):
                    await main()

        mock_run_gemini.assert_called()
        mock_git_safe.assert_called()
        mock_setup_logger.assert_called()
        mock_client_cls.assert_called()

    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_cursor", new_callable=AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_cursor_run(
        self,
        mock_init_db,
        mock_gen_id,
        mock_run_cursor,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
    ):
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        cmd = ["main.py", "--project-dir", str(self.project_dir), "--agent", "cursor", "--spec", str(self.spec_file)]
        with patch.object(sys, 'argv', cmd):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="Spec"):
                    await main()

        mock_run_cursor.assert_called()

    @patch("main.setup_logger")
    @patch("main.ensure_git_safe")
    @patch("shared.agent_client.AgentClient")
    @patch("main.run_sprint", new_callable=AsyncMock)
    @patch("shared.utils.generate_agent_id")
    @patch("shared.database.init_db")
    async def test_main_sprint_run(
        self,
        mock_init_db,
        mock_gen_id,
        mock_run_sprint,
        mock_client_cls,
        mock_git_safe,
        mock_setup_logger,
    ):
        mock_setup_logger.return_value = (MagicMock(), MagicMock())

        cmd = ["main.py", "--project-dir", str(self.project_dir), "--sprint", "--spec", str(self.spec_file)]
        with patch.object(sys, 'argv', cmd):
            # Ensure config.sprint_mode logic in main picks it up
            # We need to mock Config to ensure sprint_mode is True, OR trust that argparse sets it.
            # argparse should set args.sprint=True.

            # However, main.py does: sprint_mode=args.sprint or file_config.get("sprint_mode", False)
            # So passing --sprint should work.

            with patch.object(Path, "exists", return_value=True):
                 with patch.object(Path, "read_text", return_value="Spec"):
                        # We also need to mock Config class to prevent it from checking file existence for feature_list_path if we want precise control,
                        # but let's try relying on mocks.
                        await main()

        mock_run_sprint.assert_called()

    @patch("main.setup_logger")
    @patch("shared.utils.generate_agent_id")
    async def test_main_missing_spec_exit(self, mock_gen, mock_logger):
        mock_logger.return_value = (MagicMock(), MagicMock())

        cmd = ["main.py", "--project-dir", str(self.project_dir)] # Missing spec
        with patch.object(sys, 'argv', cmd):
            # We need to mock Config so it doesn't think feature_list exists (fresh project)
            # If feature_list exists, spec is not required.

            with patch("main.Config") as mock_config_cls:
                mock_conf = MagicMock()
                mock_conf.feature_list_path.exists.return_value = False
                mock_conf.jira = None # Ensure jira check doesn't interfere
                mock_config_cls.return_value = mock_conf

                with patch.object(Path, "exists", return_value=False):
                    with self.assertRaises(SystemExit) as cm:
                        await main()
                    self.assertEqual(cm.exception.code, 1)

    @patch("shared.config_loader.ensure_config_exists")
    @patch("shared.config_loader.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    async def test_main_show_config_command(self, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config):
        mock_load_config.return_value = {}

        cmd = ["main.py", "--project-dir", str(self.project_dir), "show-config"]
        with patch.object(sys, 'argv', cmd):
            with self.assertRaises(SystemExit) as cm:
                await main()

        self.assertEqual(cm.exception.code, 0)
        mock_json_dumps.assert_called_once()

    @patch("shared.config_loader.ensure_config_exists")
    @patch("shared.config_loader.load_config_from_file")
    @patch("shared.database.init_db")
    @patch("json.dumps", return_value="{}")
    async def test_main_dry_run_deprecation(self, mock_json_dumps, mock_init_db, mock_load_config, mock_ensure_config):
        mock_load_config.return_value = {}

        # Capture stderr to check for deprecation warning
        # Use patch on sys.stderr
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            cmd = ["main.py", "--project-dir", str(self.project_dir), "--dry-run", "--spec", str(self.spec_file)]
            with patch.object(sys, 'argv', cmd):
                 with self.assertRaises(SystemExit) as cm:
                    await main()

            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Warning: --dry-run is deprecated", mock_stderr.getvalue())

    @patch('main.run_clean')
    async def test_main_clean_list_command(self, mock_run_clean):
        # This test ensures that when 'clean --list' is invoked, the run_clean function is called.
        # The actual logic of run_clean is tested in a dedicated test below.
        cmd = ['main.py', 'clean', '--list']
        with patch.object(sys, 'argv', cmd):
            try:
                await main()
            except SystemExit:
                pass  # Expected exit if run_clean exits
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
    async def test_main_completion_command(self, mock_argcomplete):
        mock_argcomplete.shellcode.return_value = "completion_script"

        # Capture stdout using patch instead of redirect_stdout for async safety
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            cmd = ["main.py", "completion"]
            with patch.object(sys, 'argv', cmd):
                with self.assertRaises(SystemExit) as cm:
                    await main()

            self.assertEqual(cm.exception.code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("completion_script", output)


if __name__ == "__main__":
    unittest.main()
