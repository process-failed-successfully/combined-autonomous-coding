import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import yaml
import tempfile
import shutil
import os

from shared.recipes import RecipeManager

class TestRecipeManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock config file
        self.config_dir = self.test_dir / "config"
        self.config_dir.mkdir()
        self.config_path = self.config_dir / "agent_config.yaml"

        # Patch get_config_path to return our test config
        self.patcher = patch("shared.recipes.get_config_path", return_value=self.config_path)
        self.mock_get_config = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_load_empty_config(self):
        manager = RecipeManager(self.project_dir)
        self.assertEqual(manager.list_recipes(), {})

    def test_add_and_get_recipe(self):
        manager = RecipeManager(self.project_dir)
        steps = ["lint", "test"]
        manager.add_recipe("ci", steps)

        # Verify it's in memory
        self.assertEqual(manager.get_recipe("ci"), steps)

        # Verify it's on disk
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
        self.assertEqual(data["recipes"]["ci"], steps)

    def test_delete_recipe(self):
        manager = RecipeManager(self.project_dir)
        manager.add_recipe("temp", ["echo hello"])
        self.assertTrue(manager.delete_recipe("temp"))
        self.assertIsNone(manager.get_recipe("temp"))
        self.assertFalse(manager.delete_recipe("non_existent"))

    @patch("subprocess.run")
    def test_run_recipe_success(self, mock_run):
        manager = RecipeManager(self.project_dir)
        manager.add_recipe("build", ["clean", "compile"])

        mock_run.return_value.returncode = 0

        success = manager.run_recipe("build")
        self.assertTrue(success)

        # Should have called subprocess twice
        self.assertEqual(mock_run.call_count, 2)

        # Verify call args
        # The exact command depends on sys.executable, so we check loose matching
        args1 = mock_run.call_args_list[0][0][0]
        self.assertIn("clean", args1)

        args2 = mock_run.call_args_list[1][0][0]
        self.assertIn("compile", args2)

    @patch("subprocess.run")
    def test_run_recipe_failure(self, mock_run):
        manager = RecipeManager(self.project_dir)
        manager.add_recipe("deploy", ["build", "push"])

        # Fail the first step
        mock_run.return_value.returncode = 1

        success = manager.run_recipe("deploy")
        self.assertFalse(success)

        # Should stop after first failure
        self.assertEqual(mock_run.call_count, 1)

    @patch("subprocess.run")
    def test_run_recipe_recursion_limit(self, mock_run):
        manager = RecipeManager(self.project_dir)
        manager.add_recipe("loop", ["loop"]) # Infinite recursion

        # We need to mock the environment variable retrieval/setting to simulate depth
        # Since we use os.environ directly in the code, we can patch os.environ.get

        # However, for the unit test, we can just set the env var before calling
        with patch.dict(os.environ, {"AGENT_RECIPE_DEPTH": "6"}):
            success = manager.run_recipe("loop")
            self.assertFalse(success)
            mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_run_recipe_capture_output(self, mock_run):
        manager = RecipeManager(self.project_dir)
        manager.add_recipe("build", ["make"])

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Building..."
        mock_run.return_value.stderr = ""

        success, output = manager.run_recipe("build", capture_output=True)
        self.assertTrue(success)
        self.assertIn("Building...", output)
        self.assertIn("--- Running Recipe: build ---", output)

if __name__ == "__main__":
    unittest.main()
