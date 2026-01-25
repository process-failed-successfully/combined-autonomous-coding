import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, RichLog, TextArea, Checkbox, Select
from shared.tui_regex import RegexLabTab

class RegexTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield RegexLabTab(self.project_dir)

class TestRegexLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = RegexTestApp(self.project_dir)

    async def test_initial_state(self):
        async with self.app.run_test(size=(1000, 400)) as pilot:
            tab = self.app.query_one(RegexLabTab)
            self.assertIsNotNone(tab)
            self.assertIsNotNone(tab.query_one("#regex-pattern", Input))
            self.assertIsNotNone(tab.query_one("#regex-test-string", TextArea))
            self.assertIsNotNone(tab.query_one("#regex-output", RichLog))

    async def test_match_regex(self):
        async with self.app.run_test(size=(1000, 400)) as pilot:
            tab = self.app.query_one(RegexLabTab)

            # Set Inputs
            pattern_input = tab.query_one("#regex-pattern", Input)
            pattern_input.value = r"\d+"

            test_area = tab.query_one("#regex-test-string", TextArea)
            # In Textual 0.64+, text is read/write property
            test_area.text = "There are 123 apples and 45 oranges."

            # Direct call to avoid OutOfBounds in test env
            tab.match_regex()
            await pilot.pause()

            # Verify Output (indirectly via no exception)

    async def test_match_regex_injection(self):
        """Verify that brackets in text don't crash RichLog via markup injection."""
        async with self.app.run_test(size=(1000, 400)) as pilot:
            tab = self.app.query_one(RegexLabTab)

            pattern_input = tab.query_one("#regex-pattern", Input)
            pattern_input.value = r"match"

            test_area = tab.query_one("#regex-test-string", TextArea)
            # Text containing markup-like characters
            test_area.text = "This [bold] shouldn't match but match should be highlighted"

            tab.match_regex()
            await pilot.pause()
            # If escape is missing, this would likely raise rich.errors.MarkupError or similar
            # pass implied if no exception

    @patch("shared.tui_regex.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_regex(self, mock_ask):
        async with self.app.run_test(size=(1000, 400)) as pilot:
            tab = self.app.query_one(RegexLabTab)

            # Set Inputs
            pattern_input = tab.query_one("#regex-pattern", Input)
            pattern_input.value = r"^\w+$"

            # Direct call
            await tab.explain_regex()
            await pilot.pause()

            # Verify AI called
            mock_ask.assert_called_once()
            args, kwargs = mock_ask.call_args
            self.assertIn("Explain the following regex", kwargs['query'])
            self.assertEqual(kwargs['agent_type'], "gemini")

    @patch("shared.tui_regex.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_regex(self, mock_ask):
        async with self.app.run_test(size=(1000, 400)) as pilot:
            tab = self.app.query_one(RegexLabTab)

            # Set Inputs
            test_area = tab.query_one("#regex-test-string", TextArea)
            test_area.text = "Match an email address"

            # Direct call
            await tab.generate_regex()
            await pilot.pause()

            # Verify AI called
            mock_ask.assert_called_once()
            args, kwargs = mock_ask.call_args
            self.assertIn("Generate a Python regex", kwargs['query'])
            self.assertIn("Match an email address", kwargs['query'])

if __name__ == "__main__":
    unittest.main()
