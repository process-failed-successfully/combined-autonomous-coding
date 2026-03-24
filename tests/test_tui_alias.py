import unittest
from unittest.mock import patch
from textual.app import App
from shared.tui_alias import AliasTab
from textual.widgets import Select, Input, RichLog


class DummyApp(App):
    def compose(self):
        yield AliasTab()


class TestTuiAlias(unittest.IsolatedAsyncioTestCase):

    @patch("shared.tui_alias.run_alias_lab_logic")
    async def test_alias_generation(self, mock_run_logic):
        # Setup mock to output something to stdout and return True
        def mock_logic(args, commands):
            import sys
            sys.stdout.write(f"alias {args.prefix}test='test'\n")
            return True
        mock_run_logic.side_effect = mock_logic

        app = DummyApp()
        async with app.run_test() as pilot:
            # wait for mount
            await pilot.pause()

            tab = app.query_one(AliasTab)
            shell_select = tab.query_one("#alias-shell", Select)
            prefix_input = tab.query_one("#alias-prefix", Input)
            log = tab.query_one("#alias-log", RichLog)

            # Change values
            # Textual Select might be tricky to set value directly without await, let's just set it
            shell_select.value = "zsh"
            prefix_input.value = "ag-"

            # Click generate
            await pilot.click("#btn-generate-aliases")
            await pilot.pause()

            # Check output
            lines = list(log.lines)
            content = "\\n".join(str(line) for line in lines)
            # RichLog uses Strip with formatting.
            self.assertIn("alias ag-", content)
            self.assertIn("test", content)

    @patch("shared.tui_alias.run_alias_lab_logic")
    async def test_alias_generation_failure(self, mock_run_logic):
        # Setup mock to fail
        mock_run_logic.return_value = False

        app = DummyApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Click generate
            await pilot.click("#btn-generate-aliases")
            await pilot.pause()

            # Verify notification
            self.assertTrue(any(n.message == "Failed to generate aliases." for n in app._notifications))

    async def test_alias_generation_blank_shell(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            tab = app.query_one(AliasTab)
            shell_select = tab.query_one("#alias-shell", Select)
            shell_select.clear()

            # Click generate
            await pilot.click("#btn-generate-aliases")
            await pilot.pause()

            # Verify notification
            self.assertTrue(any(n.message == "Please select a target shell." for n in app._notifications))
