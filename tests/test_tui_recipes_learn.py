import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input
from shared.tui import RecipesTab

class TestRecipesLearn(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock RecipeManager
        self.patcher_rm = patch("shared.tui.RecipeManager")
        self.mock_rm_class = self.patcher_rm.start()
        self.mock_rm = self.mock_rm_class.return_value

        # Mock behavior for list_recipes to avoid errors during mount
        self.mock_rm.list_recipes.return_value = {}

        # Mock RecipeLearner
        self.patcher_rl = patch("shared.tui.RecipeLearner")
        self.mock_rl_class = self.patcher_rl.start()
        self.mock_rl = self.mock_rl_class.return_value
        self.mock_rl.learn_from_run = AsyncMock(return_value=True)

    def tearDown(self):
        self.patcher_rm.stop()
        self.patcher_rl.stop()
        shutil.rmtree(self.test_dir)

    async def test_learn_recipe_ui(self):
        """Test the 'Learn from Last Run' flow."""
        tab = RecipesTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # 1. Enter name
            name_inp = app.query_one("#recipe-new-name", Input)
            name_inp.value = "auto-recipe"

            # 2. Click Learn button
            await pilot.click("#btn-recipe-learn")

            # 3. Verify Learner was called
            # We need to verify RecipeLearner was instantiated with project_dir
            self.mock_rl_class.assert_called_with(self.project_dir)

            # Verify learn_from_run called with correct args
            self.mock_rl.learn_from_run.assert_called_with(None, "auto-recipe")

            # 4. Verify list reload (RecipeManager.list_recipes called again)
            # It's called once on mount, and once after learn
            self.assertGreaterEqual(self.mock_rm.list_recipes.call_count, 2)

            # 5. Verify input cleared
            self.assertEqual(name_inp.value, "")

if __name__ == "__main__":
    unittest.main()
