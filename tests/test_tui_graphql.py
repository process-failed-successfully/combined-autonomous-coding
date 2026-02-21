import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.widgets import Input, TextArea, RichLog, Tree
from shared.tui_graphql import GraphQLLabTab

class TestGraphQLLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = GraphQLLabTab()

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_action_send_success(self, MockManager):
        # Setup Mocks
        mock_input_url = MagicMock(spec=Input)
        mock_input_url.value = "http://test.com/graphql"

        mock_input_headers = MagicMock(spec=Input)
        mock_input_headers.value = ""

        mock_query = MagicMock(spec=TextArea)
        mock_query.text = "{ query }"

        mock_vars = MagicMock(spec=TextArea)
        mock_vars.text = ""

        mock_log = MagicMock(spec=RichLog)

        # Mock query_one
        def query_one_side_effect(selector, type=None):
            if selector == "#gql-url-input": return mock_input_url
            if selector == "#gql-headers-input": return mock_input_headers
            if selector == "#gql-query-editor": return mock_query
            if selector == "#gql-vars-editor": return mock_vars
            if selector == "#gql-response-log": return mock_log
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Mock Manager Response
        mock_instance = MockManager.return_value
        mock_instance.execute.return_value = {
            "ok": True,
            "status_code": 200,
            "elapsed": 0.1,
            "json": {"data": {"foo": "bar"}}
        }

        # Run
        await self.tab.action_send()

        # Assertions
        mock_instance.execute.assert_called_with("{ query }", {})
        mock_log.write.assert_called()

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_action_introspect_success(self, MockManager):
        # Setup Mocks
        mock_input_url = MagicMock(spec=Input)
        mock_input_url.value = "http://test.com/graphql"

        mock_input_headers = MagicMock(spec=Input)
        mock_input_headers.value = ""

        mock_tree = MagicMock(spec=Tree)
        mock_root = MagicMock()
        mock_tree.root = mock_root

        # Mock query_one
        def query_one_side_effect(selector, type=None):
            if selector == "#gql-url-input": return mock_input_url
            if selector == "#gql-headers-input": return mock_input_headers
            if selector == "#gql-schema-tree": return mock_tree
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)
        self.tab.notify = MagicMock()

        # Mock Manager Response
        mock_instance = MockManager.return_value
        mock_instance.introspect.return_value = {
            "ok": True,
            "json": {
                "data": {
                    "__schema": {
                        "types": [{"name": "User", "kind": "OBJECT"}],
                        "directives": []
                    }
                }
            }
        }

        # Run
        await self.tab.action_introspect()

        # Assertions
        mock_instance.introspect.assert_called_once()
        self.tab.notify.assert_called_with("Schema loaded.")
        mock_root.add.assert_any_call("Types")

    @patch("shared.tui_graphql.GraphQLLabManager")
    async def test_action_send_invalid_url(self, MockManager):
        mock_input_url = MagicMock(spec=Input)
        mock_input_url.value = "" # Empty
        mock_input_headers = MagicMock(spec=Input)
        mock_input_headers.value = ""

        def query_one_side_effect(selector, type=None):
            if selector == "#gql-url-input": return mock_input_url
            if selector == "#gql-headers-input": return mock_input_headers
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)
        self.tab.notify = MagicMock()

        await self.tab.action_send()

        self.tab.notify.assert_called_with("URL required", severity="error")
        MockManager.assert_not_called()

if __name__ == "__main__":
    unittest.main()
