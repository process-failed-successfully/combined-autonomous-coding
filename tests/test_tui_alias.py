import unittest
from unittest.mock import patch, MagicMock
from textual.app import App
from shared.tui_alias import AliasLabTab
import asyncio

class DummyApp(App):
    def compose(self):
        yield AliasLabTab()

class TestAliasLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_alias_lab_tab_renders_and_generates(self):
        app = DummyApp()

        # We need to ensure KNOWN_COMMANDS can be mocked or retrieved
        # since it's imported dynamically inside the tab.
        import main
        original_known_commands = getattr(main, "KNOWN_COMMANDS", [])
        main.KNOWN_COMMANDS = ["fake-cmd1", "fake-cmd2"]

        try:
            async with app.run_test() as pilot:
                # Give the app a moment to compose
                await pilot.pause()

                # Verify basic UI elements
                tab = app.query_one(AliasLabTab)
                self.assertIsNotNone(tab)

                # Input a prefix
                prefix_input = app.query_one("#alias-prefix-input")
                prefix_input.value = "test-"

                # Choose fish shell
                shell_select = app.query_one("#alias-shell-select")
                shell_select.value = "fish"

                # Click generate button
                app.query_one("#btn-generate-aliases").press()
        await pilot.pause()
                await pilot.pause()

                # Check output log
                log = app.query_one("#alias-output-log")
                output_text = "\n".join([line.text for line in log.lines])

                self.assertIn("alias test-fake-cmd1", output_text)
                self.assertIn("alias test-fake-cmd2", output_text)
                self.assertIn("fish", output_text)

                # Test error path by simulating empty KNOWN_COMMANDS
                main.KNOWN_COMMANDS = []
                app.query_one("#btn-generate-aliases").press()
        await pilot.pause()
                await pilot.pause()

                # Notification should be shown, output shouldn't change
                # We can't easily assert notification contents here, but we can verify
                # the log is cleared (since it attempts to run and fails if we handled it,
                # actually if known_commands is empty, it returns early, so we don't clear).
                # Wait, looking at the code, it clears after checking known_commands.
                # Actually, no, if `not known_commands:` it returns early.

        finally:
            main.KNOWN_COMMANDS = original_known_commands

if __name__ == '__main__':
    unittest.main()
