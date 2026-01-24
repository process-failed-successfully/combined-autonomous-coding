import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys

# Ensure main is importable
from main import run_recipes

class TestMainRecipes(unittest.IsolatedAsyncioTestCase):
    @patch('sys.exit')
    @patch('shared.recipe_learner.RecipeLearner')
    async def test_run_recipes_learn_success(self, mock_learner_cls, mock_exit):
        # Setup
        mock_learner = mock_learner_cls.return_value
        mock_learner.learn_from_run = AsyncMock(return_value=True)

        args = MagicMock()
        args.action = "learn"
        args.name = "my_recipe"
        args.run_id = "run123"
        args.agent = "gemini"
        args.model = None

        # Act
        await run_recipes(args)

        # Assert
        mock_learner_cls.assert_called()
        mock_learner.learn_from_run.assert_awaited_with(
            run_id="run123",
            recipe_name="my_recipe",
            agent_type="gemini",
            model=None
        )
        mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('shared.recipe_learner.RecipeLearner')
    async def test_run_recipes_learn_failure(self, mock_learner_cls, mock_exit):
        # Setup
        mock_learner = mock_learner_cls.return_value
        mock_learner.learn_from_run = AsyncMock(return_value=False)

        args = MagicMock()
        args.action = "learn"
        args.name = "my_recipe"
        args.run_id = None
        args.agent = "gemini"
        args.model = None

        # Act
        await run_recipes(args)

        # Assert
        mock_exit.assert_called_with(1)

    @patch('sys.exit')
    @patch('shared.recipes.RecipeManager')
    async def test_run_recipes_run_success(self, mock_manager_cls, mock_exit):
        # Setup
        mock_manager = mock_manager_cls.return_value
        mock_manager.run_recipe.return_value = True

        args = MagicMock()
        args.action = "run"
        args.name = "test_recipe"
        args.dry_run = False

        # Act
        await run_recipes(args)

        # Assert
        mock_manager.run_recipe.assert_called_with("test_recipe", dry_run=False)
        mock_exit.assert_called_with(0)

    @patch('sys.exit')
    @patch('shared.recipes.RecipeManager')
    async def test_run_recipes_run_failure(self, mock_manager_cls, mock_exit):
        # Setup
        mock_manager = mock_manager_cls.return_value
        mock_manager.run_recipe.return_value = False

        args = MagicMock()
        args.action = "run"
        args.name = "test_recipe"
        args.dry_run = False

        # Act
        await run_recipes(args)

        # Assert
        mock_manager.run_recipe.assert_called_with("test_recipe", dry_run=False)
        mock_exit.assert_called_with(1)

if __name__ == "__main__":
    unittest.main()
