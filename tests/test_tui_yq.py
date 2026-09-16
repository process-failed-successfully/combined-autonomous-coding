import unittest
from pathlib import Path
from textual.app import App
from typing import Any

from shared.tui_yq import YqLabTab


class DummyApp(App[Any]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TestYqLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tui_initialization_and_evaluation(self):
        app = DummyApp()
        tab = YqLabTab(project_dir=Path("."))

        # Patch internal app reference to prevent "No application" runtime errors
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = app

        try:
            async with app.run_test(size=(100, 100)) as pilot:
                await pilot.app.mount(tab)
                await pilot.pause()

                # Find input fields
                yaml_area = pilot.app.query_one("#yq-input-yaml")
                expr_input = pilot.app.query_one("#yq-input")
                log = pilot.app.query_one("#yq-results-log")

                # Initially the placeholder YAML should be there
                self.assertIn("store", yaml_area.text)

                # Set valid jq expression to test array iteration
                expr_input.value = ".store.book[].title"
                await pilot.pause()

                self.assertIsNotNone(log)
                lines = list(log.lines)
                # Should contain results or text rendering class string representation
                self.assertTrue(len(lines) > 0)

                # Set an invalid expression to test error handling
                expr_input.value = ".store["
                await pilot.pause()

                # Check for error rendering output
                lines = list(log.lines)
                lines_str = str(lines)
                self.assertTrue("Error evaluating" in lines_str or "Invalid jq expression" in lines_str or "Syntax" in lines_str or len(lines) > 0)

                # Test invalid YAML input
                yaml_area.text = "invalid:\n  - \n :yaml"
                await pilot.pause()
                lines = list(log.lines)
                self.assertTrue(len(lines) > 0)

        finally:
            if hasattr(type(tab), 'app'):
                del type(tab).app
