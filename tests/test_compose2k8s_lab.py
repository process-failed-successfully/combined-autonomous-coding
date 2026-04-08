import pytest
import yaml
import argparse
import sys
from unittest.mock import patch, mock_open
from io import StringIO

from shared.compose2k8s_lab import Compose2K8sManager, run_compose2k8s_lab_logic


def test_compose2k8s_basic_conversion():
    manager = Compose2K8sManager()
    compose_yaml = '''version: "3"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
'''
    result = manager.generate_k8s_manifests(compose_yaml)

    # Check that both a Deployment and a Service are created
    docs = list(yaml.safe_load_all(result))
    assert len(docs) == 2

    deployment = docs[0]
    assert deployment['kind'] == 'Deployment'
    assert deployment['metadata']['name'] == 'web'
    assert deployment['spec']['template']['spec']['containers'][0]['image'] == 'nginx:latest'
    assert deployment['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort'] == 80

    service = docs[1]
    assert service['kind'] == 'Service'
    assert service['metadata']['name'] == 'web'
    assert service['spec']['ports'][0]['port'] == 80
    assert service['spec']['ports'][0]['targetPort'] == 80


def test_compose2k8s_environment_variables():
    manager = Compose2K8sManager()
    compose_yaml = '''version: "3"
services:
  app:
    image: myapp:1.0
    environment:
      - DEBUG=1
      - API_KEY=secret
'''
    result = manager.generate_k8s_manifests(compose_yaml)
    docs = list(yaml.safe_load_all(result))

    # Only deployment since no ports mapped
    assert len(docs) == 1

    deployment = docs[0]
    env = deployment['spec']['template']['spec']['containers'][0]['env']
    assert len(env) == 2
    assert env[0]['name'] == 'DEBUG'
    assert env[0]['value'] == '1'
    assert env[1]['name'] == 'API_KEY'
    assert env[1]['value'] == 'secret'


def test_compose2k8s_no_ports_no_service():
    manager = Compose2K8sManager()
    compose_yaml = '''version: "3"
services:
  worker:
    image: worker:latest
'''
    result = manager.generate_k8s_manifests(compose_yaml)
    docs = list(yaml.safe_load_all(result))

    assert len(docs) == 1
    assert docs[0]['kind'] == 'Deployment'


def test_compose2k8s_invalid_yaml():
    manager = Compose2K8sManager()
    compose_yaml = '''version: "3"
services:
  web:
   image: nginx:latest
  - invalid
'''
    result = manager.generate_k8s_manifests(compose_yaml)
    assert "Error parsing Compose YAML" in result


def test_run_compose2k8s_lab_logic_text():
    args = argparse.Namespace(file=None, text='services:\n  app:\n    image: redis\n', output=None)
    with patch('sys.stdout', new=StringIO()) as fake_out:
        success = run_compose2k8s_lab_logic(args)
        assert success is True
        output = fake_out.getvalue()
        assert "kind: Deployment" in output
        assert "name: app" in output
        assert "image: redis" in output

def test_run_compose2k8s_lab_logic_file():
    args = argparse.Namespace(file='docker-compose.yml', text=None, output=None)
    mock_file_content = 'services:\n  app:\n    image: redis\n'

    with patch("builtins.open", mock_open(read_data=mock_file_content)), \
         patch('sys.stdout', new=StringIO()) as fake_out:
        success = run_compose2k8s_lab_logic(args)
        assert success is True
        output = fake_out.getvalue()
        assert "kind: Deployment" in output
        assert "image: redis" in output

def test_run_compose2k8s_lab_logic_no_input():
    args = argparse.Namespace(file=None, text=None, output=None)
    with patch('sys.stdin.isatty', return_value=True), \
         patch('sys.stderr', new=StringIO()) as fake_err:
        success = run_compose2k8s_lab_logic(args)
        assert success is False
        assert "Error: must provide docker-compose content" in fake_err.getvalue()
