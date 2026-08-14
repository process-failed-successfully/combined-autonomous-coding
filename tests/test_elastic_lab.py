import unittest
from unittest.mock import patch, MagicMock
from shared.elastic_lab import ElasticLabManager

class TestElasticLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = ElasticLabManager(host="http://localhost:9200")

    @patch("shared.elastic_lab.Elasticsearch")
    def test_connect_success(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        MockElasticsearch.return_value = mock_client

        self.assertTrue(self.manager.connect())
        MockElasticsearch.assert_called_with("http://localhost:9200")

    @patch("shared.elastic_lab.Elasticsearch")
    def test_connect_failure(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = False
        MockElasticsearch.return_value = mock_client

        self.assertFalse(self.manager.connect())

    @patch("shared.elastic_lab.Elasticsearch")
    def test_info(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {"cluster_name": "test-cluster"}
        MockElasticsearch.return_value = mock_client

        info = self.manager.info()
        self.assertEqual(info, {"cluster_name": "test-cluster"})

    @patch("shared.elastic_lab.Elasticsearch")
    def test_health(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.cluster.health.return_value = {"status": "green"}
        MockElasticsearch.return_value = mock_client

        health = self.manager.health()
        self.assertEqual(health, {"status": "green"})

    @patch("shared.elastic_lab.Elasticsearch")
    def test_indices(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.cat.indices.return_value = [{"index": "my-index", "health": "green"}]
        MockElasticsearch.return_value = mock_client

        indices = self.manager.indices()
        self.assertEqual(len(indices), 1)
        self.assertEqual(indices[0]["index"], "my-index")

    @patch("shared.elastic_lab.Elasticsearch")
    def test_search(self, MockElasticsearch):
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.search.return_value = {"hits": {"hits": [{"_id": "1", "_source": {"msg": "hello"}}]}}
        MockElasticsearch.return_value = mock_client

        result = self.manager.search("my-index", '{"query": {"match_all": {}}}')
        self.assertIn("hits", result)
        self.assertEqual(result["hits"]["hits"][0]["_id"], "1")

if __name__ == "__main__":
    unittest.main()
