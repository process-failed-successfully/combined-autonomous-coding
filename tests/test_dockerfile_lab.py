import unittest
import tempfile
import shutil
import argparse
from pathlib import Path
from unittest.mock import patch

from shared.dockerfile_lab import DockerfileLabManager, run_dockerfile_lab_logic

class TestDockerfileLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Create a dummy project file to trigger Python detection
        (self.project_dir / "requirements.txt").touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_manager_generation(self):
        manager = DockerfileLabManager(self.project_dir)
        self.assertEqual(manager.project_type, "python")

        files = manager.generate()
        self.assertIn("Dockerfile", files)
        self.assertIn("docker-compose.yml", files)
        self.assertIn(".dockerignore", files)
        self.assertIn("FROM python", files["Dockerfile"])

        # Test saving
        saved = manager.save_files(files)
        self.assertEqual(len(saved), 3)
        self.assertTrue((self.project_dir / "Dockerfile").exists())
        self.assertTrue((self.project_dir / "docker-compose.yml").exists())

    @patch("shared.dockerfile_lab.sys.exit")
    def test_run_logic_generate(self, mock_exit):
        args = argparse.Namespace(
            action="generate",
            project_dir=self.project_dir,
            dry_run=True,
            force=False
        )
        # Dry run shouldn't create files but should return True
        self.assertTrue(run_dockerfile_lab_logic(args))
        self.assertFalse((self.project_dir / "Dockerfile").exists())

        # Actual run
        args.dry_run = False
        self.assertTrue(run_dockerfile_lab_logic(args))
        self.assertTrue((self.project_dir / "Dockerfile").exists())

    @patch("main.run_tui")
    def test_run_logic_tui(self, mock_run_tui):
        args = argparse.Namespace(
            action="tui",
            project_dir=self.project_dir
        )
        self.assertTrue(run_dockerfile_lab_logic(args))
        mock_run_tui.assert_called_once_with(args, start_tab="tab-dockerfile")

    @patch("main.run_tui")
    def test_run_logic_tui_flag(self, mock_run_tui):
        args = argparse.Namespace(
            action=None,
            tui=True,
            project_dir=self.project_dir
        )
        self.assertTrue(run_dockerfile_lab_logic(args))
        mock_run_tui.assert_called_once_with(args, start_tab="tab-dockerfile")

if __name__ == '__main__':
    unittest.main()
