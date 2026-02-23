import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import io
import contextlib
from shared.regex_lab import RegexLabManager, run_regex_game_cli
from shared.regex_game import RegexGameLevel

class TestRegexLabGameCLI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = RegexLabManager()
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.regex_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_get_ai_hint(self, mock_ask):
        # Setup mock to print something when called, simulating the agent output
        def side_effect(*args, **kwargs):
            print("Use the force (regex)")
            return True
        mock_ask.side_effect = side_effect

        hint = await self.manager.get_ai_hint(
            description="Match 'abc'",
            positive_cases=["abc"],
            negative_cases=["def"],
            project_dir=self.project_dir
        )

        self.assertIn("Use the force (regex)", hint)
        mock_ask.assert_called_once()

    @patch("shared.regex_lab.input")
    @patch("shared.regex_lab.RegexGameGenerator")
    @patch("shared.regex_lab.RegexGameEngine")
    @patch("shared.regex_lab.RegexLabManager.get_ai_hint", new_callable=AsyncMock)
    async def test_run_regex_game_cli_flow(self, mock_get_hint, mock_engine_cls, mock_generator_cls, mock_input):
        # Setup Generator
        mock_generator = mock_generator_cls.return_value
        level1 = RegexGameLevel("L1", "Desc1", ["pos"], ["neg"])
        mock_generator.generate_levels.return_value = [level1]

        # Setup Engine
        mock_engine = mock_engine_cls.return_value

        # Setup Input sequence
        # 1. "hint" -> tests hint logic
        # 2. "wrong" -> tests validation fail
        # 3. "correct" -> tests validation success (level cleared)
        # 4. Loop breaks because levels exhausted (or we can mock it to return Quit if loop continues?)
        # Actually, run_regex_game_cli loops through levels.
        # If level is cleared, it goes to next level. Since we only have 1 level, it should finish.
        mock_input.side_effect = ["hint", "wrong", "correct"]

        # Setup Hint
        mock_get_hint.return_value = "Here is a hint."

        # Setup Engine Validation
        # First call ("wrong") -> Fail
        # Second call ("correct") -> Success
        def validate_side_effect(pattern, level):
            if pattern == "wrong":
                return {
                    "success": False,
                    "positive_results": [("pos", False)],
                    "negative_results": [("neg", True)], # True means passed (didn't match)
                    "error": None
                }
            elif pattern == "correct":
                return {
                    "success": True,
                    "positive_results": [("pos", True)],
                    "negative_results": [("neg", True)],
                    "error": None
                }
            return {}

        mock_engine.validate.side_effect = validate_side_effect

        # Capture stdout to verify output
        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            await run_regex_game_cli(self.project_dir)

        output = output_capture.getvalue()

        # Verify interactions
        self.assertIn("Welcome to the Regex Game", output)
        self.assertIn("Level 1: L1", output)
        self.assertIn("Here is a hint.", output) # Hint displayed
        self.assertIn("Level Cleared!", output)
        self.assertIn("Congratulations", output)

        mock_get_hint.assert_awaited_once()
        self.assertEqual(mock_input.call_count, 3)
        self.assertEqual(mock_engine.validate.call_count, 2)

    @patch("shared.regex_lab.input")
    @patch("shared.regex_lab.RegexGameGenerator")
    async def test_run_regex_game_cli_quit(self, mock_generator_cls, mock_input):
        mock_generator = mock_generator_cls.return_value
        level1 = RegexGameLevel("L1", "Desc1", [], [])
        mock_generator.generate_levels.return_value = [level1]

        mock_input.return_value = "quit"

        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            await run_regex_game_cli(self.project_dir)

        output = output_capture.getvalue()
        self.assertIn("Thanks for playing", output)

    @patch("shared.regex_lab.input")
    @patch("shared.regex_lab.RegexGameGenerator")
    async def test_run_regex_game_cli_skip(self, mock_generator_cls, mock_input):
        mock_generator = mock_generator_cls.return_value
        level1 = RegexGameLevel("L1", "Desc1", [], [])
        level2 = RegexGameLevel("L2", "Desc2", [], [])
        mock_generator.generate_levels.return_value = [level1, level2]

        # 1. "skip" level 1
        # 2. "quit" level 2
        mock_input.side_effect = ["skip", "quit"]

        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            await run_regex_game_cli(self.project_dir)

        output = output_capture.getvalue()
        self.assertIn("Skipping level", output)
        self.assertIn("Level 2: L2", output)

if __name__ == "__main__":
    unittest.main()
