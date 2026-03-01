import unittest
from unittest.mock import patch
from textual.app import App, ComposeResult
from shared.tui_random import RandomLabTab
from textual.widgets import Button, Input, TextArea


class RandomLabApp(App):
    def compose(self) -> ComposeResult:
        yield RandomLabTab()


class TestRandomLabTab(unittest.IsolatedAsyncioTestCase):

    async def test_initial_render(self):
        app = RandomLabApp()
        async with app.run_test() as pilot:
            # Check if main sections are rendered
            self.assertTrue(pilot.app.query_one("#pane-numbers"))
            self.assertTrue(pilot.app.query_one("#pane-strings"))
            self.assertTrue(pilot.app.query_one("#pane-uuids"))
            self.assertTrue(pilot.app.query_one("#pane-fun"))
            self.assertTrue(pilot.app.query_one("#pane-choice"))

    @patch("shared.tui_random.RandomLabManager.generate_int")
    async def test_generate_int(self, mock_generate_int):
        mock_generate_int.return_value = [42]

        app = RandomLabApp()
        async with app.run_test() as pilot:
            pilot.app.query_one("#num-min", Input).value = "10"
            pilot.app.query_one("#num-max", Input).value = "50"
            pilot.app.query_one("#num-count", Input).value = "1"

            btn = pilot.app.query_one("#btn-num-int", Button)
            btn.press()
            await pilot.pause()

            mock_generate_int.assert_called_once_with(10, 50, 1)
            output = pilot.app.query_one("#random-output", TextArea).text
            self.assertIn("42", output)

    @patch("shared.tui_random.RandomLabManager.generate_string")
    async def test_generate_string(self, mock_generate_string):
        mock_generate_string.return_value = ["random_str"]

        app = RandomLabApp()
        async with app.run_test() as pilot:
            pilot.app.query_one("#str-length", Input).value = "10"
            pilot.app.query_one("#str-count", Input).value = "1"

            btn = pilot.app.query_one("#btn-str-generate", Button)
            btn.press()
            await pilot.pause()

            mock_generate_string.assert_called_once_with(10, "alnum", 1)
            output = pilot.app.query_one("#random-output", TextArea).text
            self.assertIn("random_str", output)

    @patch("shared.tui_random.RandomLabManager.generate_uuid")
    async def test_generate_uuid(self, mock_generate_uuid):
        mock_generate_uuid.return_value = ["mock-uuid-1234"]

        app = RandomLabApp()
        async with app.run_test() as pilot:
            btn = pilot.app.query_one("#btn-uuid-generate", Button)
            btn.press()
            await pilot.pause()

            mock_generate_uuid.assert_called_once_with(4, 1)
            output = pilot.app.query_one("#random-output", TextArea).text
            self.assertIn("mock-uuid-1234", output)

    @patch("shared.tui_random.RandomLabManager.flip_coin")
    async def test_flip_coin(self, mock_flip_coin):
        mock_flip_coin.return_value = ["Heads"]

        app = RandomLabApp()
        async with app.run_test() as pilot:
            btn = pilot.app.query_one("#btn-fun-coin", Button)
            btn.press()
            await pilot.pause()

            mock_flip_coin.assert_called_once_with(1)
            output = pilot.app.query_one("#random-output", TextArea).text
            self.assertIn("Heads", output)

    @patch("shared.tui_random.RandomLabManager.roll_dice")
    async def test_roll_dice(self, mock_roll_dice):
        mock_roll_dice.return_value = [5]

        app = RandomLabApp()
        async with app.run_test() as pilot:
            pilot.app.query_one("#fun-sides", Input).value = "20"
            btn = pilot.app.query_one("#btn-fun-dice", Button)
            btn.press()
            await pilot.pause()

            mock_roll_dice.assert_called_once_with(20, 1)
            output = pilot.app.query_one("#random-output", TextArea).text
            self.assertIn("5", output)

    async def test_clear_output(self):
        app = RandomLabApp()
        async with app.run_test() as pilot:
            output_area = pilot.app.query_one("#random-output", TextArea)
            output_area.text = "Some random data"

            btn = pilot.app.query_one("#btn-clear-output", Button)
            btn.press()
            await pilot.pause()

            self.assertEqual(output_area.text, "")


if __name__ == "__main__":
    unittest.main()
