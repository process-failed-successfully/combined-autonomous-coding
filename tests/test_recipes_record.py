import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import asyncio

# Ensure we can import main
sys.path.append(os.getcwd())
import main
from shared.recipes import RecipeManager

class TestRecipesRecord(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = RecipeManager(self.project_dir)

    @patch("main.input")
    @patch("subprocess.run")
    @patch("shared.recipes.RecipeManager.add_recipe")
    def test_record_recipe(self, mock_add_recipe, mock_run, mock_input):
        # Setup mocks
        mock_input.side_effect = [
            "my_recipe", # Recipe name
            "ls -la",    # Shell command
            "lint",      # Agent command (known)
            "cd src",    # CD command
            "echo 'in src'", # Shell command in src
            "stop"       # Finish
        ]

        mock_run.return_value.returncode = 0

        # Args
        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "record"
        args.name = None # Will prompt

        # Mock path resolution
        with patch("pathlib.Path.resolve", return_value=self.project_dir):
             with patch("pathlib.Path.is_dir", return_value=True): # For cd src
                with self.assertRaises(SystemExit) as cm:
                    asyncio.run(main.run_recipes(args))

        self.assertEqual(cm.exception.code, 0)

        # Verify add_recipe call
        mock_add_recipe.assert_called_once()
        name, steps = mock_add_recipe.call_args[0]
        self.assertEqual(name, "my_recipe")
        self.assertEqual(steps, ["ls -la", "lint", "cd src", "echo 'in src'"])

    @patch("subprocess.run")
    def test_run_recipe_logic(self, mock_run):
        # Test the new logic in shared/recipes.py

        steps = ["ls", "lint", "cd src", "pwd"]
        self.manager.get_recipe = MagicMock(return_value=steps)

        mock_run.return_value.returncode = 0

        known = ["lint"]

        # We need to simulate the directory existence for cd src
        with patch("pathlib.Path.is_dir", return_value=True):
             self.manager.run_recipe("test", known_commands=known)

        # Verify calls
        # 1. ls -> shell=True
        # 2. lint -> python main.py lint (shell=False)
        # 3. cd src -> no subprocess
        # 4. pwd -> shell=True, cwd=src

        self.assertEqual(mock_run.call_count, 3)

        # Call 1: ls
        args1, kwargs1 = mock_run.call_args_list[0]
        self.assertEqual(args1[0], "ls")
        self.assertTrue(kwargs1.get("shell"))

        # Call 2: lint
        args2, kwargs2 = mock_run.call_args_list[1]
        self.assertIsInstance(args2[0], list)
        self.assertEqual(args2[0][-1], "lint") # ends with lint
        self.assertFalse(kwargs2.get("shell", False))

        # Call 3: pwd
        args3, kwargs3 = mock_run.call_args_list[2]
        self.assertEqual(args3[0], "pwd")
        self.assertTrue(kwargs3.get("shell"))
        # Check cwd updated
        self.assertEqual(kwargs3["cwd"], self.project_dir / "src")

if __name__ == '__main__':
    unittest.main()
