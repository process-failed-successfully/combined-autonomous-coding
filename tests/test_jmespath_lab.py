import unittest
import json
from pathlib import Path
from shared.jmespath_lab import JmesPathLabManager
from shared.tui_jmespath import JmesPathLabTab
from textual.app import App, ComposeResult
from typing import Any

class DummyApp(App[Any]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = Path(".")

    def compose(self) -> ComposeResult:
        yield JmesPathLabTab(project_dir=self.project_dir)

class TestJmesPathLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = JmesPathLabManager()
        self.data = {
            "locations": [
                {"name": "Seattle", "state": "WA"},
                {"name": "New York", "state": "NY"},
                {"name": "Bellevue", "state": "WA"},
                {"name": "Olympia", "state": "WA"}
            ]
        }

    def test_evaluate_basic(self):
        expr = "locations[0].name"
        result = self.manager.evaluate(self.data, expr)
        self.assertEqual(result, "Seattle")

    def test_evaluate_filter(self):
        expr = "locations[?state == 'WA'].name | sort(@)"
        result = self.manager.evaluate(self.data, expr)
        self.assertEqual(result, ["Bellevue", "Olympia", "Seattle"])

    def test_evaluate_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.evaluate(self.data, "invalid_expr[")

class TestJmesPathLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_evaluate_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Simulate typing JSON data and expression
            json_input = app.query_one("#jmespath-input-json")
            expr_input = app.query_one("#jmespath-input")
            log = app.query_one("#jmespath-results-log")

            json_input.text = '{"foo": [{"bar": 1}, {"bar": 2}]}'
            expr_input.value = "foo[*].bar"
            await pilot.pause(0.1)

            output = str(list(log.lines))
            self.assertIn("1", output)
            self.assertIn("2", output)
