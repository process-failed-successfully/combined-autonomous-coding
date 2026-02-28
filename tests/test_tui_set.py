import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
import sys

from shared.tui_set import SetLabTab
from textual.widgets import TextArea, RadioSet, Switch

class SetLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield SetLabTab()

class TestSetLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_process_sets(self):
        app = SetLabTestApp()
        async with app.run_test() as pilot:
            # Set inputs
            app.query_one("#set1_input", TextArea).text = "a\nb"
            app.query_one("#set2_input", TextArea).text = "b\nc"

            # Check operation radio button
            radio = app.query_one("#radio_union")
            self.assertTrue(radio.value)

            # Mock the backend
            mock_manager = MagicMock()
            mock_manager.process_sets.return_value = {"success": True, "result": ["a", "b", "c"], "is_boolean": False}
            with patch("shared.tui_set.SetLabManager", return_value=mock_manager):
                # Click process button
                await pilot.click("#process_btn")
                await pilot.pause()

            # Verify output
            result_area = app.query_one("#set_result", TextArea)
            self.assertEqual(result_area.text, "a\nb\nc")

    async def test_process_boolean_sets(self):
        app = SetLabTestApp()
        async with app.run_test() as pilot:
            # Set inputs
            app.query_one("#set1_input", TextArea).text = "a"
            app.query_one("#set2_input", TextArea).text = "a\nb"

            # Check operation radio button
            await pilot.click("#radio_subset")
            await pilot.pause()

            # Mock the backend
            mock_manager = MagicMock()
            mock_manager.process_sets.return_value = {"success": True, "result": ["True"], "is_boolean": True}
            with patch("shared.tui_set.SetLabManager", return_value=mock_manager):
                # Click process button
                await pilot.click("#process_btn")
                await pilot.pause()

            # Verify output
            result_area = app.query_one("#set_result", TextArea)
            self.assertEqual(result_area.text, "True")
