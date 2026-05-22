import unittest
import argparse
from io import StringIO
from unittest.mock import patch
import os
import sys

# Ensure shared can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.nginx_lab import run_nginx_lab_logic  # noqa: E402


class TestNginxLabCli(unittest.TestCase):
    def test_cli_proxy(self):
        args = argparse.Namespace(
            command="nginx-lab",
            action="proxy",
            server_name="test.local",
            backend="http://127.0.0.1:8080",
            port=8080
        )
        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_nginx_lab_logic(args)
            self.assertTrue(success)
            self.assertIn("server_name test.local;", fake_out.getvalue())
            self.assertIn("proxy_pass http://127.0.0.1:8080;", fake_out.getvalue())

    def test_cli_static(self):
        args = argparse.Namespace(
            command="nginx-lab",
            action="static",
            server_name="static.local",
            root="/var/www",
            port=80
        )
        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_nginx_lab_logic(args)
            self.assertTrue(success)
            self.assertIn("server_name static.local;", fake_out.getvalue())
            self.assertIn("root /var/www;", fake_out.getvalue())

    def test_cli_loadbalancer(self):
        args = argparse.Namespace(
            command="nginx-lab",
            action="loadbalancer",
            upstreams=["server1:80", "server2:80"],
            port=80
        )
        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_nginx_lab_logic(args)
            self.assertTrue(success)
            self.assertIn("server server1:80;", fake_out.getvalue())
            self.assertIn("server server2:80;", fake_out.getvalue())


if __name__ == '__main__':
    unittest.main()
