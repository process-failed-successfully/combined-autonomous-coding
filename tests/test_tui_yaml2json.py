import unittest
from typing import Any
from textual.app import App
from textual.widgets import TextArea, Select, Static
from shared.tui_yaml2json import Yaml2JsonLabTab


class DummyApp(App[Any]):
    def compose(self):
        yield Yaml2JsonLabTab()


class TestTuiYaml2Json(unittest.IsolatedAsyncioTestCase):
    async def test_convert_yaml2json(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2JsonLabTab)
            mode_select = tab.query_one("#yaml2json-mode-select", Select)
            input_ta = tab.query_one("#yaml2json-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2json-output-ta", TextArea)
            status_static = tab.query_one("#yaml2json-status", Static)

            mode_select.value = "yaml2json"
            input_ta.text = "key: value"
            await tab.action_convert()

            self.assertIn('"key": "value"', output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_json2yaml(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2JsonLabTab)
            mode_select = tab.query_one("#yaml2json-mode-select", Select)
            input_ta = tab.query_one("#yaml2json-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2json-output-ta", TextArea)
            status_static = tab.query_one("#yaml2json-status", Static)

            mode_select.value = "json2yaml"
            input_ta.text = '{"key": "value"}'
            await tab.action_convert()

            self.assertIn("key: value", output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_invalid_input(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2JsonLabTab)
            mode_select = tab.query_one("#yaml2json-mode-select", Select)
            input_ta = tab.query_one("#yaml2json-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2json-output-ta", TextArea)
            status_static = tab.query_one("#yaml2json-status", Static)

            mode_select.value = "json2yaml"
            input_ta.text = '{invalid'
            await tab.action_convert()

            self.assertEqual(output_ta.text, "")
            self.assertIn("Error", str(status_static.render()))


if __name__ == '__main__':
    unittest.main()
