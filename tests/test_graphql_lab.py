import unittest
from unittest.mock import MagicMock, patch
from shared.graphql_lab import GraphQLLabManager

class TestGraphQLLab(unittest.TestCase):

    def setUp(self):
        self.url = "http://localhost/graphql"
        self.manager = GraphQLLabManager(self.url)

    @patch("shared.graphql_lab.requests.post")
    def test_execute_query_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"hello": "world"}}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_post.return_value = mock_response

        result = self.manager.execute("{ hello }")

        self.assertTrue(result["ok"])
        self.assertEqual(result["json"]["data"]["hello"], "world")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["query"], "{ hello }")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    @patch("shared.graphql_lab.requests.post")
    def test_execute_query_variables(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"user": {"name": "Alice"}}}
        mock_post.return_value = mock_response

        query = "query getUser($id: ID!) { user(id: $id) { name } }"
        variables = {"id": "123"}
        self.manager.execute(query, variables)

        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["variables"], variables)

    @patch("shared.graphql_lab.requests.post")
    def test_execute_query_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.json.return_value = {"errors": [{"message": "Syntax Error"}]}
        mock_post.return_value = mock_response

        result = self.manager.execute("{ bad }")

        self.assertFalse(result["ok"])
        self.assertEqual(result["status_code"], 400)
        self.assertEqual(result["json"]["errors"][0]["message"], "Syntax Error")

    @patch("shared.graphql_lab.requests.post")
    def test_introspect(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"__schema": {"types": []}}}
        mock_post.return_value = mock_response

        result = self.manager.introspect()

        self.assertTrue(result["ok"])
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("query IntrospectionQuery", kwargs["json"]["query"])

if __name__ == '__main__':
    unittest.main()
