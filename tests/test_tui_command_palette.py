import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil

from textual.app import App
from textual.widgets import ListView, Label
from shared.tui_command_palette import AgentCommandPalette, PaletteCommand
from shared.tui import AgentTUI


class TestCommandPalette(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock dependencies to avoid side effects during AgentTUI init
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

        self.patcher_km = patch("shared.tui.KnowledgeManager")
        self.mock_km = self.patcher_km.start()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_km.stop()
        shutil.rmtree(self.test_dir)

    async def test_filtering(self):
        commands = [
            PaletteCommand("Test Command", "test_action"),
            PaletteCommand("Another Command", "another_action"),
            PaletteCommand("Quit", "quit"),
        ]

        palette = AgentCommandPalette(commands)

        class PaletteApp(App):
            def on_mount(self):
                self.push_screen(palette)

        app = PaletteApp()

        async with app.run_test() as pilot:
            # Wait for screen to be pushed
            await pilot.pause()

            # Use app.screen which should be the palette
            current_screen = app.screen
            self.assertIsInstance(current_screen, AgentCommandPalette)

            list_view = current_screen.query_one(ListView)
            self.assertEqual(len(list_view.children), 3)

            # Filter
            await pilot.press("A", "n", "o", "t", "h", "e", "r")

            # Wait for reactive update
            await pilot.pause()

            self.assertEqual(len(list_view.children), 1)

            # Check label content
            label = list_view.children[0].query_one(Label)
            self.assertIn("Another Command", str(label.render()))

    async def test_tui_integration(self):
        app = AgentTUI(project_dir=self.project_dir)

        async with app.run_test() as pilot:
            # Wait for app to be ready
            await pilot.pause()

            # Open palette with key binding
            await pilot.press("f1")
            await pilot.pause()

            # Check that the current screen is AgentCommandPalette
            self.assertIsInstance(app.screen, AgentCommandPalette)

            palette = app.screen
            # Use query_one to check existence, but don't assign if unused
            palette.query_one(ListView)

            # Filter for "Dashboard"
            await pilot.press("D", "a", "s", "h")
            await pilot.pause()

            # Select first item (Go to Dashboard)
            await pilot.press("enter")
            await pilot.pause()

            # Should be back to main screen
            self.assertNotIsInstance(app.screen, AgentCommandPalette)

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    async def test_run_tests_command(self, mock_popen, mock_run):
        # Setup mock_run to avoid ReleaseTab crash
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        app = AgentTUI(project_dir=self.project_dir)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open palette
            await pilot.press("f1")
            await pilot.pause()

            # Filter for "Run Tests"
            await pilot.press("R", "u", "n", " ", "T", "e", "s", "t", "s")
            await pilot.pause()

            # Select
            await pilot.press("enter")
            await pilot.pause()

            # Verify command execution
            self.assertTrue(mock_popen.called, "subprocess.Popen was not called")

            # Check if called with expected args
            found = False
            for call in mock_popen.call_args_list:
                args, _ = call
                if args and "main.py" in args[0] and "test" in args[0]:
                    found = True
                    break
            self.assertTrue(found, "subprocess.Popen not called with test command")

            # Verify it dismissed
            self.assertNotIsInstance(app.screen, AgentCommandPalette)


if __name__ == "__main__":
    unittest.main()
