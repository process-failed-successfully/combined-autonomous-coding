import unittest
from typing import Any
from textual.app import App
from textual.widgets import TextArea, Select, Static
from shared.tui_yaml2toml import Yaml2TomlLabTab


class DummyApp(App[Any]):
    def compose(self):
        yield Yaml2TomlLabTab()


class TestTuiYaml2Toml(unittest.IsolatedAsyncioTestCase):
    async def test_convert_yaml2toml(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2TomlLabTab)
            mode_select = tab.query_one("#yaml2toml-mode-select", Select)
            input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2toml-output-ta", TextArea)
            status_static = tab.query_one("#yaml2toml-status", Static)

            mode_select.value = "yaml2toml"
            input_ta.text = "key: value"
            await tab.action_convert()

            self.assertIn('key = "value"', output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_toml2yaml(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2TomlLabTab)
            mode_select = tab.query_one("#yaml2toml-mode-select", Select)
            input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2toml-output-ta", TextArea)
            status_static = tab.query_one("#yaml2toml-status", Static)

            mode_select.value = "toml2yaml"
            input_ta.text = 'key = "value"'
            await tab.action_convert()

            self.assertIn("key: value", output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_invalid_input(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Yaml2TomlLabTab)
            mode_select = tab.query_one("#yaml2toml-mode-select", Select)
            input_ta = tab.query_one("#yaml2toml-input-ta", TextArea)
            output_ta = tab.query_one("#yaml2toml-output-ta", TextArea)
            status_static = tab.query_one("#yaml2toml-status", Static)

            mode_select.value = "toml2yaml"
            input_ta.text = 'key = '
            await tab.action_convert()

            self.assertEqual(output_ta.text, "")
            self.assertIn("Error", str(status_static.render()))


if __name__ == '__main__':
    unittest.main()
