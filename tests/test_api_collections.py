import unittest
import json
import tempfile
import shutil
from pathlib import Path
from shared.api_collections import ApiCollectionManager

class TestApiCollectionManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = ApiCollectionManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_initialization(self):
        """Test that the manager initializes with a default collection."""
        self.assertTrue(self.manager.file_path.name == ".agent_api_collections.json")
        self.assertIn("collections", self.manager.collections)
        self.assertEqual(len(self.manager.collections["collections"]), 1)
        self.assertEqual(self.manager.collections["collections"][0]["name"], "Default")

    def test_save_and_list_request(self):
        """Test saving a request and listing it."""
        self.manager.save_request(
            name="Test Request",
            method="GET",
            url="http://example.com",
            headers={"Content-Type": "application/json"},
            body="{}"
        )

        requests = self.manager.list_requests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["name"], "Test Request")
        self.assertEqual(requests[0]["method"], "GET")
        self.assertEqual(requests[0]["url"], "http://example.com")
        self.assertIsNotNone(requests[0]["id"])

        # Verify file persistence
        with open(self.manager.file_path, "r") as f:
            data = json.load(f)
            self.assertEqual(len(data["collections"][0]["requests"]), 1)

    def test_get_request(self):
        """Test retrieving a specific request."""
        self.manager.save_request("Req 1", "GET", "url1", {}, "")
        requests = self.manager.list_requests()
        req_id = requests[0]["id"]

        req = self.manager.get_request(req_id)
        self.assertIsNotNone(req)
        self.assertEqual(req["name"], "Req 1")

    def test_delete_request(self):
        """Test deleting a request."""
        self.manager.save_request("Req 1", "GET", "url1", {}, "")
        requests = self.manager.list_requests()
        req_id = requests[0]["id"]

        success = self.manager.delete_request(req_id)
        self.assertTrue(success)

        requests_after = self.manager.list_requests()
        self.assertEqual(len(requests_after), 0)

        # Delete non-existent
        success_fail = self.manager.delete_request("fake-id")
        self.assertFalse(success_fail)

if __name__ == "__main__":
    unittest.main()
