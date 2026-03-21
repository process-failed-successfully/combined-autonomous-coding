import unittest
from textual.app import App
from shared.tui_punycode import PunycodeLabTab


class DummyApp(App):
    def compose(self):
        yield PunycodeLabTab()


class TestTuiPunycode(unittest.IsolatedAsyncioTestCase):
    async def test_punycode_encode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PunycodeLabTab)
            tab.query_one("#punycode-input").value = "münchen.de"
            tab.query_one("#mode-encode").value = True
            await pilot.click("#btn-punycode-process")
            self.assertEqual(str(tab.query_one("#punycode-output").render()), "xn--mnchen-3ya.de")

    async def test_punycode_decode(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PunycodeLabTab)
            tab.query_one("#punycode-input").value = "xn--mnchen-3ya.de"
            tab.query_one("#mode-decode").value = True
            await pilot.click("#btn-punycode-process")
            self.assertEqual(str(tab.query_one("#punycode-output").render()), "münchen.de")

    async def test_punycode_clear(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PunycodeLabTab)
            tab.query_one("#punycode-input").value = "test"
            tab.query_one("#punycode-output").update("test")
            await pilot.click("#btn-punycode-clear")
            self.assertEqual(tab.query_one("#punycode-input").value, "")
            self.assertEqual(str(tab.query_one("#punycode-output").render()), "")


if __name__ == "__main__":
    unittest.main()
