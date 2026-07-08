import pytest
import argparse
from unittest.mock import patch, mock_open
from shared.dockerfile_lab import DockerfileLabManager, run_dockerfile_lab_logic

def test_generate_dockerfile_basic():
    manager = DockerfileLabManager()
    result = manager.generate_dockerfile(base_image="ubuntu:latest")

    expected = (
        "FROM ubuntu:latest\n\n"
        "WORKDIR /app\n\n"
        "COPY . .\n"
    )
    assert result == expected

def test_generate_dockerfile_python():
    manager = DockerfileLabManager()
    result = manager.generate_dockerfile(
        base_image="python:3.11",
        project_type="python",
        ports=["8080"],
        env_vars=["PYTHONUNBUFFERED=1"],
        cmd="python main.py"
    )

    expected = (
        "FROM python:3.11\n\n"
        "WORKDIR /app\n\n"
        "ENV PYTHONUNBUFFERED=\"1\"\n\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        "COPY . .\n\n"
        "EXPOSE 8080\n\n"
        "CMD python main.py\n"
    )
    assert result == expected

def test_run_dockerfile_lab_logic_generate(capsys):
    args = argparse.Namespace(
        action="generate",
        base_image="node:18",
        type="node",
        workdir="/src",
        ports="3000,8080",
        env="NODE_ENV=production,DEBUG=true",
        entrypoint="[\"npm\", \"start\"]",
        cmd="",
        output=None
    )

    success = run_dockerfile_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    output = captured.out

    assert "FROM node:18" in output
    assert "WORKDIR /src" in output
    assert "ENV NODE_ENV=\"production\"" in output
    assert "ENV DEBUG=\"true\"" in output
    assert "COPY package*.json ./" in output
    assert "RUN npm install" in output
    assert "EXPOSE 3000" in output
    assert "EXPOSE 8080" in output
    assert "ENTRYPOINT [\"npm\", \"start\"]" in output

@patch("builtins.open", new_callable=mock_open)
def test_run_dockerfile_lab_logic_generate_to_file(mock_open, capsys):
    args = argparse.Namespace(
        action="generate",
        base_image="alpine:latest",
        type="generic",
        workdir="/app",
        ports=None,
        env=None,
        entrypoint="",
        cmd="",
        output="Dockerfile"
    )

    success = run_dockerfile_lab_logic(args)
    assert success is True

    mock_open.assert_called_once_with("Dockerfile", "w", encoding="utf-8")
    handle = mock_open()
    handle.write.assert_called()

    captured = capsys.readouterr()
    assert "✅ Dockerfile written to Dockerfile" in captured.out
