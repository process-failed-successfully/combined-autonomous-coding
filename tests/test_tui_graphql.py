import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_graphql import GraphQLLabTab
from textual.widgets import Input, TextArea, RichLog

class GraphQLLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield GraphQLLabTab()

class TestGraphQLLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_compose(self):
        app = GraphQLLabTestApp()
        async with app.run_test() as pilot:
            self.assertIsNotNone(app.query_one(GraphQLLabTab))
            self.assertIsNotNone(app.query_one("#gql-url", Input))
            self.assertIsNotNone(app.query_one("#gql-query-editor", TextArea))
            self.assertIsNotNone(app.query_one("#btn-gql-execute"))

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_execute_query(self, MockManager):
        # Setup mock
        mock_instance = MockManager.return_value
        mock_instance.execute = MagicMock(return_value={
            "ok": True,
            "status_code": 200,
            "elapsed": 0.5,
            "json": {"data": {"hello": "world"}}
        })

        app = GraphQLLabTestApp()
        async with app.run_test() as pilot:
            # Set inputs
            app.query_one("#gql-url").press()
        await pilot.pause()
            app.query_one("#gql-url", Input).value = "http://test.com/graphql"

            app.query_one("#gql-query-editor", TextArea).text = "query { hello }"

            # Click execute
            app.query_one("#btn-gql-execute").press()
        await pilot.pause()

            # Verify manager called
            MockManager.assert_called_with("http://test.com/graphql", {})
            mock_instance.execute.assert_called_with("query { hello }", None)

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_introspect(self, MockManager):
        # Setup mock
        mock_instance = MockManager.return_value
        mock_instance.introspect = MagicMock(return_value={
            "ok": True,
            "status_code": 200,
            "json": {"data": {"__schema": {}}}
        })

        app = GraphQLLabTestApp()
        async with app.run_test() as pilot:
            app.query_one("#gql-url", Input).value = "http://test.com/graphql"

            app.query_one("#btn-gql-introspect").press()
        await pilot.pause()

            mock_instance.introspect.assert_called_once()

    async def test_validation(self):
        app = GraphQLLabTestApp()
        async with app.run_test() as pilot:
            # Missing URL
            # Note: In a real app we might mock self.notify to verify the message
            # For now we ensure it doesn't crash
            app.query_one("#btn-gql-execute").press()
        await pilot.pause()

            app.query_one("#gql-url", Input).value = "http://valid.com"
            # Missing query
            app.query_one("#btn-gql-execute").press()
        await pilot.pause()
