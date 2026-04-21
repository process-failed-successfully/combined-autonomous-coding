import unittest
from typing import Any
from textual.app import App
from textual.widgets import TextArea, Select, Static
from shared.tui_json2yaml import Json2YamlLabTab

class DummyApp(App[Any]):
    def compose(self):
        yield Json2YamlLabTab()

class TestTuiJson2Yaml(unittest.IsolatedAsyncioTestCase):
    async def test_convert_json2yaml(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Json2YamlLabTab)
            mode_select = tab.query_one("#json2yaml-mode-select", Select)
            input_ta = tab.query_one("#json2yaml-input-ta", TextArea)
            output_ta = tab.query_one("#json2yaml-output-ta", TextArea)
            status_static = tab.query_one("#json2yaml-status", Static)

            mode_select.value = "json2yaml"
            input_ta.text = '{"key": "value"}'
            await tab.action_convert()

            self.assertIn("key: value", output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_yaml2json(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Json2YamlLabTab)
            mode_select = tab.query_one("#json2yaml-mode-select", Select)
            input_ta = tab.query_one("#json2yaml-input-ta", TextArea)
            output_ta = tab.query_one("#json2yaml-output-ta", TextArea)
            status_static = tab.query_one("#json2yaml-status", Static)

            mode_select.value = "yaml2json"
            input_ta.text = "key: value"
            await tab.action_convert()

            self.assertIn('"key": "value"', output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_invalid_input(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Json2YamlLabTab)
            mode_select = tab.query_one("#json2yaml-mode-select", Select)
            input_ta = tab.query_one("#json2yaml-input-ta", TextArea)
            output_ta = tab.query_one("#json2yaml-output-ta", TextArea)
            status_static = tab.query_one("#json2yaml-status", Static)

            mode_select.value = "json2yaml"
            input_ta.text = '{invalid'
            await tab.action_convert()

            self.assertEqual(output_ta.text, "")
            self.assertIn("Error", str(status_static.render()))

if __name__ == '__main__':
    unittest.main()
