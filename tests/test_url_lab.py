import unittest
from shared.url_lab import UrlLabManager

class TestUrlLab(unittest.TestCase):
    def setUp(self):
        self.manager = UrlLabManager()

    def test_parse(self):
        url = "https://user:pass@example.com:8080/path/to/resource?query=param&key=value#fragment"
        result = self.manager.parse(url)
        self.assertEqual(result["scheme"], "https")
        self.assertEqual(result["netloc"], "user:pass@example.com:8080")
        self.assertEqual(result["path"], "/path/to/resource")
        self.assertEqual(result["query"], "query=param&key=value")
        self.assertEqual(result["fragment"], "fragment")
        self.assertEqual(result["hostname"], "example.com")
        self.assertEqual(result["port"], 8080)
        self.assertEqual(result["username"], "user")
        self.assertEqual(result["password"], "pass")
        self.assertEqual(result["query_params"]["query"], "param")

    def test_encode_decode(self):
        original = "hello world/?"
        encoded = self.manager.encode(original)
        self.assertEqual(encoded, "hello%20world/%3F")
        decoded = self.manager.decode(encoded)
        self.assertEqual(decoded, original)

    def test_join(self):
        base = "https://example.com/base/"
        path = "path/to/resource"
        joined = self.manager.join(base, path)
        self.assertEqual(joined, "https://example.com/base/path/to/resource")

        base = "https://example.com/base" # no trailing slash
        joined = self.manager.join(base, path)
        self.assertEqual(joined, "https://example.com/path/to/resource")

    def test_update_params(self):
        url = "https://example.com?a=1&b=2"

        # Add
        new_url = self.manager.update_params(url, add={"c": "3"})
        self.assertIn("c=3", new_url)
        self.assertIn("a=1", new_url)

        # Update
        new_url = self.manager.update_params(url, add={"a": "4"})
        self.assertIn("a=4", new_url)
        self.assertNotIn("a=1", new_url)

        # Remove
        new_url = self.manager.update_params(url, remove=["b"])
        self.assertNotIn("b=2", new_url)
        self.assertIn("a=1", new_url)

    def test_normalize(self):
        url = "HTTP://Example.COM:80/Path/?b=2&a=1"
        normalized = self.manager.normalize(url)
        self.assertEqual(normalized, "http://example.com/Path/?a=1&b=2")

        url_https = "HTTPS://Example.COM:443/Path"
        normalized = self.manager.normalize(url_https)
        self.assertEqual(normalized, "https://example.com/Path")

if __name__ == '__main__':
    unittest.main()
