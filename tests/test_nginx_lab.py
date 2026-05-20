import pytest
import subprocess
import sys
import os
from shared.nginx_lab import NginxLabManager

def test_nginx_generate_proxy():
    manager = NginxLabManager()
    output = manager.generate_proxy("example.com", 8080)
    assert "server_name example.com;" in output
    assert "proxy_pass http://localhost:8080;" in output

def test_nginx_generate_static():
    manager = NginxLabManager()
    output = manager.generate_static("example.com", "/var/www/html")
    assert "server_name example.com;" in output
    assert "root /var/www/html;" in output

def test_nginx_generate_loadbalancer():
    manager = NginxLabManager()
    output = manager.generate_loadbalancer("example.com", ["10.0.0.1:80", "10.0.0.2:80"])
    assert "server 10.0.0.1:80;" in output
    assert "server 10.0.0.2:80;" in output
    assert "server_name example.com;" in output
    assert "proxy_pass http://backend_servers;" in output

def test_nginx_cli_proxy():
    env = os.environ.copy()
    env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
    result = subprocess.run(
        [sys.executable, "main.py", "nginx-lab", "proxy", "--domain", "test.com", "--port", "3000"],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0
    assert "server_name test.com;" in result.stdout
    assert "proxy_pass http://localhost:3000;" in result.stdout

def test_nginx_cli_static():
    env = os.environ.copy()
    env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
    result = subprocess.run(
        [sys.executable, "main.py", "nginx-lab", "static", "--domain", "test.com", "--path", "/path/to/static"],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0
    assert "server_name test.com;" in result.stdout
    assert "root /path/to/static;" in result.stdout

def test_nginx_cli_loadbalancer():
    env = os.environ.copy()
    env["PYTHONPATH"] = f".{os.pathsep}{env.get('PYTHONPATH', '')}"
    result = subprocess.run(
        [sys.executable, "main.py", "nginx-lab", "loadbalancer", "--domain", "test.com", "--upstreams", "server1:80, server2:80"],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0
    assert "server_name test.com;" in result.stdout
    assert "server server1:80;" in result.stdout
    assert "server server2:80;" in result.stdout
