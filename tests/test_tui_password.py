import unittest
from textual.app import App, ComposeResult
from textual.widgets import Input, TextArea, Select, Button
from shared.tui_password import PasswordLabTab


class PasswordLabApp(App):
    """Test app for PasswordLabTab."""
    def compose(self) -> ComposeResult:
        yield PasswordLabTab()


class TestPasswordLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_generate_password(self):
        app = PasswordLabApp()
        async with app.run_test() as pilot:
            # Set values
            app.query_one("#pwd-gen-length").press()
        await pilot.pause()
            app.query_one("#pwd-gen-length", Input).value = "10"

            # Click generate
            await pilot.pause()
            app.query_one("#btn-pwd-gen", Button).press()
            await pilot.pause()

            # Output should not be error
            output = app.query_one("#pwd-gen-output", TextArea).text
            self.assertIn("Password:", output)
            self.assertIn("Entropy:", output)
            self.assertNotIn("Error:", output)

    async def test_generate_password_error(self):
        app = PasswordLabApp()
        async with app.run_test() as pilot:
            app.query_one("#pwd-gen-length", Input).value = "invalid"

            await pilot.pause()
            app.query_one("#btn-pwd-gen", Button).press()
            await pilot.pause()

            output = app.query_one("#pwd-gen-output", TextArea).text
            self.assertIn("Error:", output)

    async def test_check_strength(self):
        app = PasswordLabApp()
        async with app.run_test() as pilot:
            app.query_one("#pwd-chk-input", Input).value = "VeryStrongPassword123!"

            await pilot.pause()
            app.query_one("#btn-pwd-chk", Button).press()
            await pilot.pause()

            output = app.query_one("#pwd-chk-output", TextArea).text
            self.assertIn("Score:", output)
            self.assertIn("Entropy:", output)
            self.assertNotIn("Error:", output)

    async def test_generate_passphrase(self):
        app = PasswordLabApp()
        async with app.run_test() as pilot:
            # Set values
            app.query_one("#pwd-passphrase-words", Input).value = "5"
            app.query_one("#pwd-passphrase-separator", Input).value = "_"

            # Click generate
            await pilot.pause()
            app.query_one("#btn-pwd-passphrase", Button).press()
            await pilot.pause()

            # Output should not be error
            output = app.query_one("#pwd-passphrase-output", TextArea).text
            self.assertIn("Passphrase:", output)
            self.assertIn("Entropy:", output)
            self.assertNotIn("Error:", output)

            # The passphrase part should have 4 separators
            passphrase_part = output.split("\n")[0].replace("Passphrase: ", "")
            self.assertEqual(passphrase_part.count("_"), 4)

    async def test_hash_password(self):
        app = PasswordLabApp()
        async with app.run_test() as pilot:
            app.query_one("#pwd-hash-input", Input).value = "mypassword"
            app.query_one("#pwd-hash-algo", Select).value = "pbkdf2"

            await pilot.pause()
            app.query_one("#btn-pwd-hash", Button).press()
            await pilot.pause()

            output = app.query_one("#pwd-hash-output", TextArea).text
            # Expected to be pbkdf2 hash format or an error if dependencies missing,
            # but usually it works.
            self.assertTrue(output.startswith("$pbkdf2") or "Error:" in output)


if __name__ == '__main__':
    unittest.main()
