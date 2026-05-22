import unittest
import os
import sys

# Ensure shared can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Only run if textual is installed to prevent ModuleNotFoundError
try:
    pass
    from textual.app import App
    from shared.tui_nginx import NginxLabTab
    from textual.widgets import Select, Input, TextArea
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False


@unittest.skipIf(not HAS_TEXTUAL, "Textual library is not available")
class TestNginxLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_tui_rendering_and_action(self):
        class DummyApp(App):
            def compose(self):
                yield NginxLabTab()

        app = DummyApp()
        async with app.run_test() as pilot:
            # wait for mount
            await pilot.pause()

            # test proxy generation (default)
            select = app.query_one("#nginx_type", Select)
            self.assertEqual(select.value, "proxy")

            # Find inputs
            server_name = app.query_one("#nginx_server_name", Input)
            server_name.value = "my-site.com"

            backend = app.query_one("#nginx_backend", Input)
            backend.value = "http://localhost:3000"

            port = app.query_one("#nginx_port", Input)
            port.value = "8080"

            # Click generate
            await pilot.click("#btn_generate_nginx")
            await pilot.pause()

            # Verify output
            output = app.query_one("#nginx_output", TextArea)
            self.assertIn("server_name my-site.com;", output.text)
            self.assertIn("proxy_pass http://localhost:3000;", output.text)
            self.assertIn("listen 8080;", output.text)


if __name__ == '__main__':
    unittest.main()
