import unittest
from textual.app import App
from shared.tui_plist import PlistLabTab
from textual.widgets import Select, TextArea, Static

class PlistApp(App):
    def compose(self):
        yield PlistLabTab()

class TestTuiPlist(unittest.IsolatedAsyncioTestCase):
    async def test_convert_plist2json(self):
        app = PlistApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PlistLabTab)
            mode_select = tab.query_one("#plist-mode-select", Select)
            input_ta = tab.query_one("#plist-input-ta", TextArea)
            output_ta = tab.query_one("#plist-output-ta", TextArea)
            status_static = tab.query_one("#plist-status", Static)

            mode_select.value = "plist2json"
            input_ta.load_text('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n\t<key>hello</key>\n\t<string>world</string>\n</dict>\n</plist>\n')

            await pilot.click("#plist-convert-btn")
            await pilot.pause(0.1)

            self.assertIn('"hello": "world"', output_ta.text)
            self.assertIn("Conversion successful.", str(status_static.render()))

if __name__ == "__main__":
    unittest.main()
