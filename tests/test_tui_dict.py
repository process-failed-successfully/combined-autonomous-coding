import unittest
from unittest.mock import patch, MagicMock
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, RichLog
from shared.tui_dict import DictLabTab

class MockDictLabApp(App[None]):
    def compose(self) -> ComposeResult:
        yield DictLabTab()

class TestDictLabTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = MockDictLabApp()

    async def test_initial_render(self):
        async with self.app.run_test():
            self.assertIsNotNone(self.app.query_one("#dict-input"))
            self.assertIsNotNone(self.app.query_one("#btn-define"))
            self.assertIsNotNone(self.app.query_one("#btn-synonyms"))
            self.assertIsNotNone(self.app.query_one("#btn-antonyms"))
            self.assertIsNotNone(self.app.query_one("#dict-log"))

    @patch('shared.dict_lab.DictLabManager.lookup')
    @patch('shared.dict_lab.DictLabManager.get_definitions')
    async def test_define_word(self, mock_get_defs, mock_lookup):
        mock_lookup.return_value = {"success": True, "data": []}
        mock_get_defs.return_value = [
            {"part_of_speech": "noun", "phonetic": "həˈləʊ", "definition": "Greeting.", "example": ""}
        ]

        async with self.app.run_test() as pilot:
            input_widget = self.app.query_one("#dict-input", Input)
            input_widget.value = "hello"

            self.app.query_one("#btn-define").press()
            await pilot.pause()

            log = self.app.query_one("#dict-log", RichLog)
            content = "\n".join([line.text for line in log.lines])

            self.assertIn("Greeting.", content)

    @patch('shared.dict_lab.DictLabManager.lookup')
    @patch('shared.dict_lab.DictLabManager.get_synonyms')
    async def test_synonyms_word(self, mock_get_synonyms, mock_lookup):
        mock_lookup.return_value = {"success": True, "data": []}
        mock_get_synonyms.return_value = ["hi", "greeting"]

        async with self.app.run_test() as pilot:
            input_widget = self.app.query_one("#dict-input", Input)
            input_widget.value = "hello"

            self.app.query_one("#btn-synonyms").press()
            await pilot.pause()

            log = self.app.query_one("#dict-log", RichLog)
            content = "\n".join([line.text for line in log.lines])

            self.assertIn("hi, greeting", content)

    @patch('shared.dict_lab.DictLabManager.lookup')
    async def test_not_found(self, mock_lookup):
        mock_lookup.return_value = {"success": False, "error": "Word 'xyz' not found."}

        async with self.app.run_test() as pilot:
            input_widget = self.app.query_one("#dict-input", Input)
            input_widget.value = "xyz"

            self.app.query_one("#btn-define").press()
            await pilot.pause()

            log = self.app.query_one("#dict-log", RichLog)
            content = "\n".join([line.text for line in log.lines])

            self.assertIn("Word 'xyz' not found.", content)

if __name__ == '__main__':
    unittest.main()
