import unittest
from unittest.mock import patch, MagicMock

from textual.widgets import TextArea, Input, Static
from shared.tui_json2graphql import Json2GraphQLLabTab

class TestJson2GraphQLLabTab(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_json2graphql.Json2GraphQLManager")
        self.MockManager = self.patcher.start()

        self.tab = Json2GraphQLLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        mock_app = MagicMock()
        self.tab._app = mock_app
        type(self.tab).app = mock_app

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_convert_success(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = '{"name": "test"}'

        output_area = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "Root"

        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2graphql-input-ta": return input_area
            if selector == "#json2graphql-output-ta": return output_area
            if selector == "#json2graphql-name-input": return name_input
            if selector == "#json2graphql-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.generate.return_value = "type Root {\n  name: String\n}"

        await self.tab.action_convert()

        self.mock_manager.generate.assert_called_with('{"name": "test"}', "Root")
        self.assertEqual(output_area.text, "type Root {\n  name: String\n}")
        status_static.update.assert_called_with("[green]Conversion successful.[/green]")

    async def test_convert_empty_input(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = '   '

        output_area = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "Root"

        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2graphql-input-ta": return input_area
            if selector == "#json2graphql-output-ta": return output_area
            if selector == "#json2graphql-name-input": return name_input
            if selector == "#json2graphql-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        await self.tab.action_convert()

        self.mock_manager.generate.assert_not_called()
        self.assertEqual(output_area.text, "")
        status_static.update.assert_called_with("[yellow]Input JSON is empty.[/yellow]")

    async def test_convert_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = 'invalid json'

        output_area = MagicMock(spec=TextArea)
        name_input = MagicMock(spec=Input)
        name_input.value = "Root"

        status_static = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#json2graphql-input-ta": return input_area
            if selector == "#json2graphql-output-ta": return output_area
            if selector == "#json2graphql-name-input": return name_input
            if selector == "#json2graphql-status": return status_static
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.generate.side_effect = ValueError("Invalid JSON")

        await self.tab.action_convert()

        self.mock_manager.generate.assert_called_with('invalid json', "Root")
        self.assertEqual(output_area.text, "")
        status_static.update.assert_called_with("[red]Invalid JSON[/red]")

if __name__ == "__main__":
    unittest.main()
