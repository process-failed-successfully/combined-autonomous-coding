import unittest
from unittest.mock import MagicMock
from shared.tui_bcrypt import BcryptLabTab
from textual.app import App
from textual.widgets import Input, Select, TextArea, Static

class DummyApp(App):
    def compose(self):
        yield BcryptLabTab()

class TestTuiBcrypt(unittest.IsolatedAsyncioTestCase):
    async def test_bcrypt_generate(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(BcryptLabTab)

            # Find inputs
            pw_input = tab.query_one("#bcrypt-gen-password", Input)
            rounds_select = tab.query_one("#bcrypt-rounds", Select)
            gen_btn = tab.query_one("#btn-bcrypt-generate")
            result_area = tab.query_one("#bcrypt-gen-result", TextArea)

            # Fill in
            pw_input.value = "mysecurepw"
            rounds_select.value = 4

            # Click generate
            pilot.app.query_one("#btn-bcrypt-generate").press()
            await pilot.pause()

            # Check result
            hashed = result_area.text
            self.assertTrue(hashed.startswith("$2b$04$"))

    async def test_bcrypt_verify(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(BcryptLabTab)

            # First generate a hash
            hashed = tab.manager.hash_password("mysecurepw", rounds=4)

            # Verify correct password
            pw_input = tab.query_one("#bcrypt-ver-password", Input)
            hash_input = tab.query_one("#bcrypt-ver-hash", Input)
            result_lbl = tab.query_one("#bcrypt-ver-result", Static)

            pw_input.value = "mysecurepw"
            hash_input.value = hashed

            pilot.app.query_one("#btn-bcrypt-verify").press()
            await pilot.pause()

            self.assertIn("Match: True", str(result_lbl.render()))

            # Verify wrong password
            pw_input.value = "wrongpw"
            pilot.app.query_one("#btn-bcrypt-verify").press()
            await pilot.pause()

            self.assertIn("Match: False", str(result_lbl.render()))
