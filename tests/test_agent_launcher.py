import pytest
from typer.testing import CliRunner
import sys
from pathlib import Path

# Ensure bin is in sys.path to import agent
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from bin.agent import app

runner = CliRunner()


def test_app_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "First-Class Agent Launcher" in result.stdout
    assert "run" in result.stdout
    assert "list" in result.stdout


@pytest.fixture
def mock_config_path(tmp_path, monkeypatch):
    config_file = tmp_path / "agent_config.yaml"
    monkeypatch.setattr("bin.agent.get_config_path", lambda: config_file)
    monkeypatch.setattr("bin.agent.ensure_config_exists", lambda: config_file.touch() if not config_file.exists() else None)
    return config_file


def test_config_set(mock_config_path):
    result = runner.invoke(app, ["config", "set", "max-iterations", "50"])
    assert result.exit_code == 0
    assert "Set max-iterations = 50" in result.stdout

    import yaml
    with open(mock_config_path, "r") as f:
        data = yaml.safe_load(f)
    assert data["max-iterations"] == 50


def test_config_view(mock_config_path):
    import yaml
    with open(mock_config_path, "w") as f:
        yaml.dump({"test_key": "test_value"}, f)

    result = runner.invoke(app, ["config", "view"])
    assert result.exit_code == 0
    assert "test_key: test_value" in result.stdout


def test_config_reset(mock_config_path):
    import yaml
    with open(mock_config_path, "w") as f:
        yaml.dump({"model": "gemini-1.5-pro", "other": "value"}, f)

    result = runner.invoke(app, ["config", "reset", "model"])
    assert result.exit_code == 0
    assert "Reset model" in result.stdout

    with open(mock_config_path, "r") as f:
        data = yaml.safe_load(f)
    assert "model" not in data
    assert data["other"] == "value"


def test_config_list_keys():
    result = runner.invoke(app, ["config", "list-keys"])
    assert result.exit_code == 0
    assert "agent_type" in result.stdout
    assert "max_iterations" in result.stdout
    assert "timeout" in result.stdout
    # Should exclude internal keys
    assert "project_dir" not in result.stdout
    assert "jira_ticket_key" not in result.stdout

# Mock Docker and Subprocess for other commands


@pytest.fixture(autouse=True)
def mock_docker_subprocess(monkeypatch):
    def mock_run(cmd, *args, **kwargs):
        pass

    def mock_popen(cmd, *args, **kwargs):
        pass

    monkeypatch.setattr("bin.agent.subprocess.run", mock_run)
    monkeypatch.setattr("bin.agent.subprocess.Popen", mock_popen)

    class MockContainer:
        def __init__(self, name, short_id, status, tags):
            self.name = name
            self.short_id = short_id
            self.status = status

            class MockImage:
                def __init__(self, t):
                    self.tags = t
            self.image = MockImage(tags)

        def stop(self):
            pass

    class MockDockerClient:
        class MockContainers:
            def list(self, all=False):
                return [
                    MockContainer("test_agent_run", "123", "running", ["tag1"]),
                    MockContainer("other_container", "456", "stopped", ["tag2"])
                ]

            def get(self, name):
                if name == "test_agent_run":
                    return MockContainer("test_agent_run", "123", "running", ["tag1"])
                import docker
                raise docker.errors.NotFound(f"Container {name} not found")

        def __init__(self):
            self.containers = self.MockContainers()

    def mock_get_docker_client():
        return MockDockerClient()

    monkeypatch.setattr("bin.agent.get_docker_client", mock_get_docker_client)


def test_list():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "test_agent_run" in result.stdout
    assert "123" in result.stdout
    # other_container should not be listed as it doesn't match filter
    assert "other_container" not in result.stdout


def test_attach_success():
    result = runner.invoke(app, ["attach", "test_agent_run"])
    assert result.exit_code == 0
    assert "Attaching to test_agent_run..." in result.stdout


def test_attach_not_found():
    result = runner.invoke(app, ["attach", "nonexistent"])
    assert result.exit_code == 0
    assert "Container nonexistent not found" in result.stdout


def test_logs_success():
    result = runner.invoke(app, ["logs", "test_agent_run"])
    assert result.exit_code == 0
    assert "Fetching logs for test_agent_run..." in result.stdout


def test_stop_success():
    result = runner.invoke(app, ["stop", "test_agent_run"])
    assert result.exit_code == 0
    assert "Stopping test_agent_run..." in result.stdout
    assert "test_agent_run stopped successfully" in result.stdout


def test_run_command():
    result = runner.invoke(app, ["run", "--spec", "my_spec.txt", "--detached", "--name", "my_agent"])
    # With the mock, it should successfully pass through
    assert result.exit_code == 0
    assert "Agent started in background" in result.stdout
