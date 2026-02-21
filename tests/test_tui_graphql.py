import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Input, TextArea, RichLog, Tree
from shared.tui_graphql import GraphQLLabTab

class GraphQLApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield GraphQLLabTab(self.project_dir)

class TestGraphQLLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = GraphQLApp(self.project_dir)

    async def test_initialization(self):
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(GraphQLLabTab)
            self.assertIsNotNone(tab)
            self.assertIsNotNone(pilot.app.query_one("#graphql-url", Input))
            self.assertIsNotNone(pilot.app.query_one("#graphql-query-editor", TextArea))

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_execute_query(self, MockManager):
        # Setup Mock
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.execute.return_value = {
            "status_code": 200,
            "ok": True,
            "elapsed": 0.1,
            "json": {"data": {"hello": "world"}}
        }

        async with self.app.run_test() as pilot:
            # Set Inputs
            url_input = pilot.app.query_one("#graphql-url", Input)
            url_input.value = "https://example.com/graphql"

            query_editor = pilot.app.query_one("#graphql-query-editor", TextArea)
            query_editor.text = "{ hello }"

            # Click Execute
            await pilot.click("#btn-graphql-execute")

            # Allow async tasks to run
            await pilot.pause()

            # Verify Manager Call
            mock_manager_instance.execute.assert_called_with("{ hello }", None)

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_introspect_schema(self, MockManager):
        # Setup Mock
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.introspect.return_value = {
            "status_code": 200,
            "ok": True,
            "json": {
                "data": {
                    "__schema": {
                        "queryType": {"name": "Query"},
                        "types": [
                            {"kind": "OBJECT", "name": "Query", "fields": [{"name": "hello", "type": {"kind": "SCALAR", "name": "String"}}]},
                            {"kind": "SCALAR", "name": "String"}
                        ]
                    }
                }
            }
        }

        async with self.app.run_test() as pilot:
            # Set URL
            url_input = pilot.app.query_one("#graphql-url", Input)
            url_input.value = "https://example.com/graphql"

            # Click Introspect
            await pilot.click("#btn-graphql-introspect")

            await pilot.pause()

            # Verify Manager Call
            mock_manager_instance.introspect.assert_called()

            # Verify Tree Population
            tree = pilot.app.query_one("#graphql-schema-tree", Tree)
            self.assertEqual(str(tree.root.label), "Schema (https://example.com/graphql)")
            self.assertTrue(len(tree.root.children) > 0)

            query_node = next((n for n in tree.root.children if "Query" in str(n.label)), None)
            self.assertIsNotNone(query_node)
