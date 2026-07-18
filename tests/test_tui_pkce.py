import unittest
from textual.app import App, ComposeResult
from shared.tui_pkce import PkceLabTab
from textual.widgets import Input, Static, RadioSet

class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield PkceLabTab()

class TestTuiPkce(unittest.IsolatedAsyncioTestCase):
    async def test_pkce_lab_tab_initial_state(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PkceLabTab)

            # The verifier should be populated on mount
            verifier_input = tab.query_one("#input-verifier", Input)
            self.assertTrue(len(verifier_input.value) >= 43)

            # The method should default to S256
            method_radio = tab.query_one("#radio-method", RadioSet)
            self.assertEqual(method_radio.pressed_button.id, "method-s256")

            # The challenge should be populated
            challenge_input = tab.query_one("#input-challenge", Input)
            self.assertTrue(len(challenge_input.value) > 0)
            self.assertNotEqual(verifier_input.value, challenge_input.value)  # Because it's S256

    async def test_pkce_generate_verifier(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PkceLabTab)
            verifier_input = tab.query_one("#input-verifier", Input)

            initial_verifier = verifier_input.value

            # Click generate verifier
            await pilot.click("#btn-generate-verifier")

            new_verifier = verifier_input.value
            self.assertNotEqual(initial_verifier, new_verifier)
            self.assertTrue(len(new_verifier) >= 43)

    async def test_pkce_change_method(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PkceLabTab)
            verifier_input = tab.query_one("#input-verifier", Input)
            challenge_input = tab.query_one("#input-challenge", Input)

            # Initially S256
            self.assertNotEqual(verifier_input.value, challenge_input.value)

            # Click plain
            await pilot.click("#method-plain")

            # Now challenge should equal verifier
            self.assertEqual(verifier_input.value, challenge_input.value)

    async def test_pkce_verify_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PkceLabTab)
            lbl_result = tab.query_one("#lbl-result", Static)

            # Initial state should be empty
            self.assertEqual(str(lbl_result.render()), "")

            # Click verify
            await pilot.click("#btn-verify")

            # Should show valid message
            self.assertIn("Valid!", str(lbl_result.render()))

    async def test_pkce_verify_failure(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PkceLabTab)
            challenge_input = tab.query_one("#input-challenge", Input)
            lbl_result = tab.query_one("#lbl-result", Static)

            # Tamper with challenge
            challenge_input.value = "invalid-challenge-string"

            # Click verify
            await pilot.click("#btn-verify")

            # Should show invalid message
            self.assertIn("Invalid!", str(lbl_result.render()))

if __name__ == '__main__':
    unittest.main()
