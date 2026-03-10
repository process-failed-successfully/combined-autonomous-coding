import unittest
import sys
from pathlib import Path

# Add parent dir to path to find shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.http_lab import HttpLabManager

class TestHttpLabCurlGen(unittest.TestCase):
    def setUp(self):
        self.manager = HttpLabManager()

    def test_generate_curl_basic_get(self):
        cmd = self.manager.generate_curl("GET", "example.com")
        self.assertEqual(cmd, 'curl -X GET "http://example.com"')

    def test_generate_curl_with_protocol(self):
        cmd = self.manager.generate_curl("POST", "https://api.example.com/v1/users")
        self.assertEqual(cmd, 'curl -X POST "https://api.example.com/v1/users"')

    def test_generate_curl_empty_url(self):
        cmd = self.manager.generate_curl("GET", "")
        self.assertEqual(cmd, 'curl -X GET ""')

    def test_generate_curl_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token123"
        }
        cmd = self.manager.generate_curl("GET", "http://example.com", headers=headers)
        self.assertTrue('-H "Content-Type: application/json"' in cmd)
        self.assertTrue('-H "Authorization: Bearer token123"' in cmd)
        self.assertTrue(cmd.startswith('curl -X GET'))

    def test_generate_curl_with_data(self):
        data = '{"key": "value"}'
        cmd = self.manager.generate_curl("POST", "http://example.com", data=data)
        self.assertTrue("-d '{\"key\": \"value\"}'" in cmd)

    def test_generate_curl_all(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        data = '{"hello": "world"}'
        cmd = self.manager.generate_curl("PUT", "https://api.example.com", headers=headers, data=data)

        self.assertTrue('curl -X PUT' in cmd)
        self.assertTrue('-H "Content-Type: application/json"' in cmd)
        self.assertTrue('-H "Accept: */*"' in cmd)
        self.assertTrue("-d '{\"hello\": \"world\"}'" in cmd)
        self.assertTrue('"https://api.example.com"' in cmd)

if __name__ == '__main__':
    unittest.main()
