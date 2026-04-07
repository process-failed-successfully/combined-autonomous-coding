import unittest
import pytest
from pathlib import Path

from textual.app import App
from shared.tui_arn import ArnLabTab
from textual.widgets import Input, RichLog, Button

class TestArnApp(App):
    def compose(self):
        yield ArnLabTab(project_dir=Path("."))

class TestTuiArn(unittest.IsolatedAsyncioTestCase):
    async def test_arn_tab_parse_success(self):
        app = TestArnApp()
        async with app.run_test() as pilot:
            # Type into input
            parse_input = app.query_one("#arn-parse-input", Input)
            parse_input.value = "arn:aws:s3:::my-bucket"

            # Click Parse button (programmatic instead of pilot.click due to screen region issues)
            app.query_one("#btn-arn-parse", Button).press()
            await pilot.pause()

            log = app.query_one("#arn-parse-output", RichLog)
            content = "\n".join([line.text for line in log.lines])
            self.assertIn("Parse Successful", content)
            self.assertIn("my-bucket", content)

    async def test_arn_tab_parse_error(self):
        app = TestArnApp()
        async with app.run_test() as pilot:
            parse_input = app.query_one("#arn-parse-input", Input)
            parse_input.value = "invalid-arn"

            app.query_one("#btn-arn-parse", Button).press()
            await pilot.pause()

            log = app.query_one("#arn-parse-output", RichLog)
            content = "\n".join([line.text for line in log.lines])
            self.assertIn("Error:", content)

    async def test_arn_tab_construct(self):
        app = TestArnApp()
        async with app.run_test() as pilot:
            app.query_one("#arn-construct-service", Input).value = "iam"
            app.query_one("#arn-construct-resource", Input).value = "role/Admin"

            app.query_one("#btn-arn-construct", Button).press()
            await pilot.pause()

            log = app.query_one("#arn-construct-output", RichLog)
            content = "\n".join([line.text for line in log.lines])
            self.assertIn("arn:aws:iam:::role/Admin", content)

            # Verify auto-populate
            parse_input = app.query_one("#arn-parse-input", Input)
            self.assertEqual(parse_input.value, "arn:aws:iam:::role/Admin")

if __name__ == '__main__':
    unittest.main()
