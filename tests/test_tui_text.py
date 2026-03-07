import unittest
from unittest.mock import MagicMock
from textual.widgets import TextArea, Input, Label
from shared.tui_text import TextLabTab


class TestTextLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_mount(self):
        tab = TextLabTab()
        self.assertIsInstance(tab, TextLabTab)

    async def test_transform_interaction(self):
        tab = TextLabTab()
        tab.notify = MagicMock()

        # Mock query_one to return mocks
        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "hello_world"

        mock_output = MagicMock(spec=TextArea)

        def query_one_side_effect(selector, type=None):
            if selector == "#text-input":
                return mock_input
            if selector == "#text-output":
                return mock_output
            if selector == "#lbl-text-stats":
                return MagicMock(spec=Label)
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Test Camel Case Button
        event = MagicMock()
        event.button.id = "btn-case-camel"

        await tab.on_button_pressed(event)

        # Verify manager called (real manager used)
        # hello_world -> helloWorld
        self.assertEqual(mock_output.text, "helloWorld")

    async def test_encode_interaction(self):
        tab = TextLabTab()
        tab.notify = MagicMock()

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "hello world"

        mock_output = MagicMock(spec=TextArea)

        def query_one_side_effect(selector, type=None):
            if selector == "#text-input":
                return mock_input
            if selector == "#text-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Test Base64 Encode
        event = MagicMock()
        event.button.id = "btn-enc-base64-en"
        await tab.on_button_pressed(event)
        self.assertEqual(mock_output.text, "aGVsbG8gd29ybGQ=")

        # Test Base64 Decode
        mock_input.text = "aGVsbG8gd29ybGQ="
        event.button.id = "btn-enc-base64-de"
        await tab.on_button_pressed(event)
        self.assertEqual(mock_output.text, "hello world")

    async def test_extract_interaction(self):
        tab = TextLabTab()
        tab.notify = MagicMock()

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "Here is my email test@example.com."

        mock_output = MagicMock(spec=TextArea)

        def query_one_side_effect(selector, type=None):
            if selector == "#text-input":
                return mock_input
            if selector == "#text-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Test Extract Emails
        event = MagicMock()
        event.button.id = "btn-ext-email"
        await tab.on_button_pressed(event)
        self.assertEqual(mock_output.text, "test@example.com")

        # Test Extract URLs
        mock_input.text = "Check out https://github.com/path!"
        event.button.id = "btn-ext-url"
        await tab.on_button_pressed(event)
        self.assertEqual(mock_output.text, "https://github.com/path")

    async def test_filter_interaction(self):
        tab = TextLabTab()
        tab.notify = MagicMock()

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "apple\nbanana"
        mock_output = MagicMock(spec=TextArea)
        mock_pattern = MagicMock(spec=Input)
        mock_pattern.value = "app"

        def query_one_side_effect(selector, type=None):
            if selector == "#text-input":
                return mock_input
            if selector == "#text-output":
                return mock_output
            if selector == "#text-filter-pattern":
                return mock_pattern
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        event = MagicMock()
        event.button.id = "btn-filter-keep"

        await tab.on_button_pressed(event)

        self.assertEqual(mock_output.text, "apple")

    async def test_stats_interaction(self):
        tab = TextLabTab()
        tab.notify = MagicMock()

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "hello world"
        mock_label = MagicMock(spec=Label)

        def query_one_side_effect(selector, type=None):
            if selector == "#text-input":
                return mock_input
            if selector == "#lbl-text-stats":
                return mock_label
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        event = MagicMock()
        event.button.id = "btn-text-stats"

        await tab.on_button_pressed(event)

        # Verify label updated
        mock_label.update.assert_called()
        args = mock_label.update.call_args[0][0]
        self.assertIn("Length: 11", args)


if __name__ == "__main__":
    unittest.main()
