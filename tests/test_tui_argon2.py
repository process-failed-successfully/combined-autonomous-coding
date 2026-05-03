import unittest
import pytest
from unittest.mock import MagicMock
from textual.app import App
from textual.widgets import Input, Select, TextArea, Static

pytest.importorskip("argon2")
pytest.importorskip("textual")

from shared.tui_argon2 import Argon2LabTab


class DummyApp(App):
    def compose(self):
        yield Argon2LabTab()

class TestTuiArgon2(unittest.IsolatedAsyncioTestCase):
    async def test_argon2_generate(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Argon2LabTab)

            # Find inputs
            pw_input = tab.query_one("#argon2-gen-password", Input)
            time_input = tab.query_one("#argon2-time", Input)
            mem_input = tab.query_one("#argon2-memory", Input)
            par_input = tab.query_one("#argon2-parallelism", Input)
            len_input = tab.query_one("#argon2-hash-len", Input)

            gen_btn = tab.query_one("#btn-argon2-generate")
            result_area = tab.query_one("#argon2-gen-result", TextArea)

            # Fill in
            pw_input.value = "mysecurepw"
            time_input.value = "2"
            mem_input.value = "1024"
            par_input.value = "1"
            len_input.value = "16"

            # Click generate
            await pilot.click("#btn-argon2-generate")

            # Check result
            hashed = result_area.text
            self.assertTrue(hashed.startswith("$argon2id$v=19$"))

    async def test_argon2_verify(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Argon2LabTab)

            # First generate a hash
            hashed = tab.manager.hash_password("mysecurepw", time_cost=2, memory_cost=1024, parallelism=1, hash_len=16)

            # Verify correct password
            pw_input = tab.query_one("#argon2-ver-password", Input)
            hash_input = tab.query_one("#argon2-ver-hash", Input)
            result_lbl = tab.query_one("#argon2-ver-result", Static)

            pw_input.value = "mysecurepw"
            hash_input.value = hashed

            await pilot.click("#btn-argon2-verify")

            self.assertIn("Match: True", str(result_lbl.render()))

            # Verify wrong password
            pw_input.value = "wrongpw"
            await pilot.click("#btn-argon2-verify")

            self.assertIn("Match: False", str(result_lbl.render()))