import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Select, TextArea, Markdown, Label
from shared.tui_presentation import PresentationTab

class PresentationTabApp(App):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield PresentationTab(self.project_dir)

class TestPresentationTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = PresentationTabApp(self.project_dir)

    async def test_initialization(self):
        async with self.app.run_test(size=(300, 100)) as pilot:
            tab = pilot.app.query_one(PresentationTab)
            self.assertIsInstance(tab, PresentationTab)
            self.assertEqual(tab.project_dir, self.project_dir)
            self.assertEqual(tab.presentation_file, self.project_dir / "presentation.md")

    @patch("shared.tui_presentation.PresentationGenerator")
    async def test_generate_presentation(self, MockGenerator):
        # Setup mock
        mock_instance = MockGenerator.return_value
        mock_instance.generate = AsyncMock(return_value=True)

        async with self.app.run_test(size=(300, 100)) as pilot:
            # Simulate generate button click
            btn = pilot.app.query_one("#btn-pres-generate", Button)
            btn.press()
            await pilot.pause()

            # Verify generator was called
            MockGenerator.assert_called_with(self.project_dir, agent_type="gemini", model=None)
            mock_instance.generate.assert_called_once()

            # Verify file args
            call_args = mock_instance.generate.call_args
            self.assertEqual(call_args[0][0], self.project_dir / "presentation.md")
            self.assertEqual(call_args[1]['theme'], "default")

    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    async def test_save_presentation(self, mock_read, mock_exists, mock_write):
        mock_exists.return_value = False

        async with self.app.run_test(size=(300, 100)) as pilot:
            editor = pilot.app.query_one("#pres-editor", TextArea)
            editor.text = "# New Presentation"

            await pilot.click("#btn-pres-save")

            mock_write.assert_called_with("# New Presentation", encoding="utf-8")

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    async def test_load_presentation_existing(self, mock_read, mock_exists):
        mock_exists.return_value = True
        mock_read.return_value = "# Existing Presentation"

        async with self.app.run_test(size=(300, 100)) as pilot:
            editor = pilot.app.query_one("#pres-editor", TextArea)
            self.assertEqual(editor.text, "# Existing Presentation")

            preview = pilot.app.query_one("#pres-preview", Markdown)
            # Cannot easily check markdown rendered content, but verifying text update logic via editor is mostly enough for TUI logic
