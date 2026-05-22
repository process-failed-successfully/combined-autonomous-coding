import unittest
from shared.nginx_lab import NginxLabManager


class TestNginxLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = NginxLabManager()

    def test_generate_proxy(self):
        config = self.manager.generate_proxy("example.com", "http://127.0.0.1:8080", 80)
        self.assertIn("server_name example.com;", config)
        self.assertIn("proxy_pass http://127.0.0.1:8080;", config)
        self.assertIn("listen 80;", config)

    def test_generate_static(self):
        config = self.manager.generate_static("test.com", "/var/www/test", 443)
        self.assertIn("server_name test.com;", config)
        self.assertIn("root /var/www/test;", config)
        self.assertIn("listen 443;", config)

    def test_generate_loadbalancer(self):
        config = self.manager.generate_loadbalancer(["10.0.0.1:80", "10.0.0.2:80"], 8080)
        self.assertIn("upstream backend", config)
        self.assertIn("server 10.0.0.1:80;", config)
        self.assertIn("server 10.0.0.2:80;", config)
        self.assertIn("proxy_pass http://backend;", config)
        self.assertIn("listen 8080;", config)


if __name__ == '__main__':
    unittest.main()
