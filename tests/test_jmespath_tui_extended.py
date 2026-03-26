import unittest
import json
from pathlib import Path
from shared.tui_jmespath import JmesPathLabTab
from textual.app import App, ComposeResult
from typing import Any

class DummyApp(App[Any]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = Path(".")

    def compose(self) -> ComposeResult:
        yield JmesPathLabTab(project_dir=self.project_dir)

class TestJmesPathLabTabExtended(unittest.IsolatedAsyncioTestCase):
    async def test_evaluate_ui_empty_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '   '
            expr_input.value = "foo[*].bar"
            await pilot.pause(0.1)
            output = str(list(log.lines))
            self.assertEqual(output, "[]")

    async def test_evaluate_ui_empty_expr(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '{"foo": "bar"}'
            expr_input.value = "   "
            await pilot.pause(0.1)
            output = str(list(log.lines))
            self.assertEqual(output, "[]")

    async def test_evaluate_ui_invalid_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '{"foo": "bar"'
            expr_input.value = "foo"
            await pilot.pause(0.1)
            output = str(list(log.lines))
            self.assertIn("Invalid JSON", output)

    async def test_evaluate_ui_invalid_expr(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '{"foo": "bar"}'
            expr_input.value = "foo["
            await pilot.pause(0.1)
            output = str(list(log.lines))
            self.assertIn("Error evaluating JMESPath", output)

    async def test_evaluate_ui_null_result(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '{"foo": "bar"}'
            expr_input.value = "baz"
            await pilot.pause(0.1)
            output = str(list(log.lines))
            self.assertIn("null", output)
