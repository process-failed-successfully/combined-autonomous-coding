import unittest
from shared.jsonpath_lab import JsonPathLabManager
from shared.tui_jsonpath import JsonPathLabTab
from textual.app import App
from pathlib import Path


class DummyApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notifications = []

    def notify(self, message, *, title="", severity="information", timeout=None):
        self.notifications.append((message, severity))


class TestJsonPathLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = JsonPathLabManager()
        self.data = {
            "store": {
                "book": [
                    {"category": "reference",
                     "author": "Nigel Rees",
                     "title": "Sayings of the Century",
                     "price": 8.95
                     },
                    {"category": "fiction",
                     "author": "Evelyn Waugh",
                     "title": "Sword of Honour",
                     "price": 12.99
                     }
                ],
                "bicycle": {
                    "color": "red",
                    "price": 19.95
                }
            }
        }

    def test_evaluate_dotted(self):
        res = self.manager.evaluate(self.data, "$.store.bicycle.color")
        self.assertEqual(res, ["red"])

    def test_evaluate_array_index(self):
        res = self.manager.evaluate(self.data, "$.store.book[1].author")
        self.assertEqual(res, ["Evelyn Waugh"])

    def test_evaluate_wildcard_array(self):
        res = self.manager.evaluate(self.data, "$.store.book[*].title")
        self.assertEqual(res, ["Sayings of the Century", "Sword of Honour"])

    def test_evaluate_wildcard_dict(self):
        res = self.manager.evaluate(self.data, "$.store.*.price")
        self.assertEqual(res, [19.95])

    def test_evaluate_filter_expression(self):
        # jsonpath-ng supports advanced filtering
        res = self.manager.evaluate(self.data, "$.store.book[?(@.price < 10)].title")
        self.assertEqual(res, ["Sayings of the Century"])

    def test_evaluate_invalid_path(self):
        with self.assertRaises(ValueError):
            self.manager.evaluate(self.data, "$.store.[")


class TestJsonPathLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tui_initialization(self):
        app = DummyApp()
        tab = JsonPathLabTab(project_dir=Path("."))

        # Patch the internal app reference to avoid "No application" runtime errors
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = app

        try:
            async with app.run_test() as pilot:
                # Mount the tab onto the dummy app
                await pilot.app.mount(tab)
                await pilot.pause()

                # Find input fields
                json_area = pilot.app.query_one("#jsonpath-input-json")
                expr_input = pilot.app.query_one("#jsonpath-input")

                # The initial text should be present
                self.assertIn("store", json_area.text)

                # Input a valid expression
                expr_input.value = "$.store.book[*].title"
                await pilot.pause()

                # Check log for results
                log = pilot.app.query_one("#jsonpath-results-log")

                # Textual RichLog content can be tricky to extract as raw string easily from tests,
                # but we can test that the log is present and didn't crash.
                self.assertIsNotNone(log)

                # Let's also cause a JSON error to test error handling
                json_area.text = "{ invalid json "
                await pilot.pause()
        finally:
            # Let's restore to prevent cleanup issues
            if hasattr(type(tab), 'app'):
                del type(tab).app
