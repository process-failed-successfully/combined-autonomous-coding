import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DataTable, Input, RichLog
from shared.tui import RecipesTab

class TestRecipesTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock RecipeManager
        self.patcher_rm = patch("shared.tui.RecipeManager")
        self.mock_rm_class = self.patcher_rm.start()
        self.mock_rm = self.mock_rm_class.return_value

        # Default behavior
        self.mock_rm.list_recipes.return_value = {"build": ["clean", "make"]}
        self.mock_rm.get_recipe.return_value = ["clean", "make"]
        self.mock_rm.add_recipe.return_value = True
        self.mock_rm.delete_recipe.return_value = True
        self.mock_rm.run_recipe.return_value = (True, "Mock Output")

    def tearDown(self):
        self.patcher_rm.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose_and_load(self):
        """Test tab composition and initial load."""
        tab = RecipesTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Check widgets exist
            self.assertIsNotNone(app.query_one("#recipe-table"))
            self.assertIsNotNone(app.query_one("#recipe-new-name"))
            self.assertIsNotNone(app.query_one("#recipe-new-steps"))
            self.assertIsNotNone(app.query_one("#btn-recipe-create"))

            # Check load_recipes was called (on_mount)
            self.mock_rm.list_recipes.assert_called()

            # Check table content
            table = app.query_one("#recipe-table", DataTable)
            self.assertEqual(table.row_count, 1)

    async def test_create_recipe(self):
        """Test creating a recipe via UI."""
        tab = RecipesTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Input name and steps
            name_inp = app.query_one("#recipe-new-name", Input)
            name_inp.value = "deploy"

            steps_inp = app.query_one("#recipe-new-steps", Input)
            steps_inp.value = "build, push"

            # Click create
            app.query_one("#btn-recipe-create").press()
        await pilot.pause()

            # Verify manager call
            self.mock_rm.add_recipe.assert_called_with("deploy", ["build", "push"])

            # Verify reload
            self.assertEqual(self.mock_rm.list_recipes.call_count, 2) # initial load + reload

    async def test_run_recipe(self):
        """Test running a recipe."""
        tab = RecipesTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Simulate selection state manually
            tab.selected_recipe = "build"
            app.query_one("#btn-recipe-run").disabled = False

            # Click run
            app.query_one("#btn-recipe-run").press()
        await pilot.pause()

            # Verify manager run call
            self.mock_rm.run_recipe.assert_called_with("build", capture_output=True)

if __name__ == "__main__":
    unittest.main()
