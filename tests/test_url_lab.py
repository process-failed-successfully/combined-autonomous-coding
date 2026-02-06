import unittest
from shared.url_lab import UrlLabManager

class TestUrlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = UrlLabManager()

    def test_parse(self):
        url = "https://example.com/path?query=1&foo=bar#frag"
        result = self.manager.parse(url)
        self.assertEqual(result["scheme"], "https")
        self.assertEqual(result["netloc"], "example.com")
        self.assertEqual(result["path"], "/path")
        self.assertEqual(result["query_params"]["query"], "1")
        self.assertEqual(result["query_params"]["foo"], "bar")
        self.assertEqual(result["fragment"], "frag")

    def test_encode(self):
        text = "Hello World!"
        result = self.manager.encode(text)
        self.assertEqual(result, "Hello%20World%21")

    def test_decode(self):
        text = "Hello%20World%21"
        result = self.manager.decode(text)
        self.assertEqual(result, "Hello World!")

    def test_join(self):
        base = "https://example.com/api/"
        path = "v1/resource"
        result = self.manager.join(base, path)
        self.assertEqual(result, "https://example.com/api/v1/resource")

    def test_update_query_add(self):
        url = "https://example.com/search?q=test"
        add_params = ["page=2", "sort=desc"]
        new_url = self.manager.update_query(url, add_params=add_params)
        self.assertIn("page=2", new_url)
        self.assertIn("sort=desc", new_url)
        self.assertIn("q=test", new_url)

    def test_update_query_remove(self):
        url = "https://example.com/search?q=test&page=2"
        remove_params = ["page"]
        new_url = self.manager.update_query(url, remove_params=remove_params)
        self.assertNotIn("page=2", new_url)
        self.assertIn("q=test", new_url)

    def test_update_query_replace(self):
        url = "https://example.com/search?q=test"
        add_params = ["q=new"]
        new_url = self.manager.update_query(url, add_params=add_params)
        self.assertIn("q=new", new_url)
        self.assertNotIn("q=test", new_url)

if __name__ == "__main__":
    unittest.main()
