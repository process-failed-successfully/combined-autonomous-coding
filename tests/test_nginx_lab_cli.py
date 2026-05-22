import unittest
import subprocess
import sys
import os


class TestNginxLabCli(unittest.TestCase):
    def test_cli_proxy(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.getcwd()] + env.get("PYTHONPATH", "").split(os.pathsep)
        )
        result = subprocess.run(
            [sys.executable, "main.py", "nginx-lab", "proxy", "--server-name", "test.local", "--backend", "http://127.0.0.1:8080", "--port", "8080"],
            env=env,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("server_name test.local;", result.stdout)
        self.assertIn("proxy_pass http://127.0.0.1:8080;", result.stdout)

    def test_cli_static(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.getcwd()] + env.get("PYTHONPATH", "").split(os.pathsep)
        )
        result = subprocess.run(
            [sys.executable, "main.py", "nginx-lab", "static", "--server-name", "static.local", "--root", "/var/www"],
            env=env,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("server_name static.local;", result.stdout)
        self.assertIn("root /var/www;", result.stdout)

    def test_cli_loadbalancer(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.getcwd()] + env.get("PYTHONPATH", "").split(os.pathsep)
        )
        result = subprocess.run(
            [sys.executable, "main.py", "nginx-lab", "loadbalancer", "--upstreams", "server1:80", "server2:80"],
            env=env,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("server server1:80;", result.stdout)
        self.assertIn("server server2:80;", result.stdout)


if __name__ == '__main__':
    unittest.main()
