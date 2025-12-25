import subprocess
import sys
import pytest
from unittest.mock import patch

# Path to the agent CLI script
AGENT_CLI_PATH = "./bin/agent"

def test_cli_help():
    """
    Tests that the CLI's help message is displayed correctly.
    """
    result = subprocess.run([AGENT_CLI_PATH, "--help"], capture_output=True, text=True, check=True)
    assert "Autonomous Coding Agent CLI." in result.stdout
    assert "Usage: agent [OPTIONS] COMMAND [ARGS]..." in result.stdout
    assert "Commands:" in result.stdout
    assert "run      Launches the autonomous coding agent." in result.stdout
    assert "list     Lists all active/detached agents." in result.stdout
    assert "attach   Re-attaches to a running agent session." in result.stdout
    assert "logs     Tails logs of a background agent." in result.stdout
    assert "stop     Gracefully terminates a background agent." in result.stdout
    assert "config   Manages agent configuration." in result.stdout

@patch("docker.from_env")
def test_cli_run_docker_daemon_running(mock_from_env):
    """
    Tests the 'run' command when the Docker daemon is running.
    """
    mock_client = mock_from_env.return_value
    mock_client.ping.return_value = True

    result = subprocess.run([AGENT_CLI_PATH, "run"], capture_output=True, text=True, check=True)
    assert "Running agent in ." in result.stdout
    assert "Docker daemon is running." in result.stdout
    assert "Agent initialized successfully!" in result.stdout
    assert "Agent started. Monitoring progress..." in result.stdout
    assert "Agent finished." in result.stdout

@patch("docker.from_env")
def test_cli_run_docker_daemon_not_running(mock_from_env):
    """
    Tests the 'run' command when the Docker daemon is not running.
    """
    mock_client = mock_from_env.return_value
    mock_client.ping.side_effect = Exception("Docker daemon not available")

    # Expect a CalledProcessError because the script exits with code 1
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.run([AGENT_CLI_PATH, "run"], capture_output=True, text=True, check=True)
    
    assert "Cannot proceed without a running Docker daemon." in excinfo.value.stderr
    assert excinfo.value.returncode == 1

def test_cli_list():
    """
    Tests the 'list' command.
    """
    result = subprocess.run([AGENT_CLI_PATH, "list"], capture_output=True, text=True, check=True)
    assert "Listing agents..." in result.stdout

def test_cli_attach():
    """
    Tests the 'attach' command.
    """
    result = subprocess.run([AGENT_CLI_PATH, "attach", "test-agent"], capture_output=True, text=True, check=True)
    assert "Attaching to agent: test-agent" in result.stdout

def test_cli_logs():
    """
    Tests the 'logs' command.
    """
    result = subprocess.run([AGENT_CLI_PATH, "logs", "test-agent"], capture_output=True, text=True, check=True)
    assert "Viewing logs for agent: test-agent" in result.stdout

def test_cli_stop():
    """
    Tests the 'stop' command.
    """
    result = subprocess.run([AGENT_CLI_PATH, "stop", "test-agent"], capture_output=True, text=True, check=True)
    assert "Stopping agent: test-agent" in result.stdout

def test_cli_config():
    """
    Tests the 'config' command.
    """
    result = subprocess.run([AGENT_CLI_PATH, "config"], capture_output=True, text=True, check=True)
    assert "Managing configuration..." in result.stdout
