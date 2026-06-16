import unittest
from unittest.mock import MagicMock, AsyncMock
from textual.widgets import TextArea, Input, Button, Static
from shared.tui_json2zod import Json2ZodLabTab

class TestJson2ZodLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = Json2ZodLabTab()
        self.tab.query_one = MagicMock()

    async def test_convert_success(self):
        input_ta = MagicMock(spec=TextArea)
        input_ta.text = '{"name": "Alice"}'
        output_ta = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "TestSchema"
        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2zod-input-ta": return input_ta
            if selector == "#json2zod-output-ta": return output_ta
            if selector == "#json2zod-name-input": return name_input
            if selector == "#json2zod-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        await self.tab.action_convert()

        self.assertIn("export const TestSchema = z.object({", output_ta.text)
        self.assertIn("name: z.string(),", output_ta.text)
        status_static.update.assert_called_with("[green]Conversion successful.[/green]")

    async def test_convert_empty(self):
        input_ta = MagicMock(spec=TextArea)
        input_ta.text = ''
        output_ta = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "TestSchema"
        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2zod-input-ta": return input_ta
            if selector == "#json2zod-output-ta": return output_ta
            if selector == "#json2zod-name-input": return name_input
            if selector == "#json2zod-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        await self.tab.action_convert()

        self.assertEqual(output_ta.text, "")
        status_static.update.assert_called_with("[yellow]Input JSON is empty.[/yellow]")

    async def test_convert_error(self):
        input_ta = MagicMock(spec=TextArea)
        input_ta.text = 'invalid json'
        output_ta = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "TestSchema"
        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2zod-input-ta": return input_ta
            if selector == "#json2zod-output-ta": return output_ta
            if selector == "#json2zod-name-input": return name_input
            if selector == "#json2zod-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        await self.tab.action_convert()

        self.assertEqual(output_ta.text, "")
        status_static.update.assert_called()
        self.assertTrue(status_static.update.call_args[0][0].startswith("[red]Invalid JSON"))

    async def test_on_button_pressed(self):
        # We'll just verify it calls action_convert
        self.tab.action_convert = AsyncMock()
        btn = MagicMock(spec=Button)
        btn.id = "json2zod-convert-btn"
        event = MagicMock()
        event.button = btn

        await self.tab.on_button_pressed(event)

        self.tab.action_convert.assert_awaited_once()

if __name__ == "__main__":
    unittest.main()
