import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from agents.cli import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Autonomous Coding Agent CLI Launcher" in result.stdout
    assert "run" in result.stdout
    assert "list" in result.stdout
    assert "stop" in result.stdout
    assert "logs" in result.stdout

@patch("agents.cli.PreFlightCheck")
@patch("agents.cli.session_manager")
def test_cli_run_interactive(mock_session_mgr, mock_preflight):
    # Mock PreFlightCheck
    mock_checker = MagicMock()
    mock_checker.run_checks.return_value = True
    mock_preflight.return_value = mock_checker

    # Mock SessionManager
    mock_session_mgr.start_session.return_value = 0

    result = runner.invoke(app, ["run", "--name", "test-agent", "--skip-checks"])
    
    # We used skip-checks, so preflight shouldn't be called if logic is correct? 
    # Wait, cli.py says: if not skip_checks: checker = PreFlightCheck() ...
    
    assert result.exit_code == 0
    assert "Running session: test-agent" in result.stdout
    mock_session_mgr.start_session.assert_called_once()
    args = mock_session_mgr.start_session.call_args
    assert args[0][0] == "test-agent" # name
    assert args[1]["detached"] == False

@patch("agents.cli.PreFlightCheck")
@patch("agents.cli.session_manager")
def test_cli_run_detached(mock_session_mgr, mock_preflight):
    mock_checker = MagicMock()
    mock_checker.run_checks.return_value = True
    mock_preflight.return_value = mock_checker

    mock_session_mgr.start_session.return_value = {"pid": 1234, "log_file": "agent.log"}

    result = runner.invoke(app, ["run", "--name", "detached-agent", "--detached", "--skip-checks"])

    assert result.exit_code == 0
    assert "Launching detached session: detached-agent" in result.stdout
    assert "Session started!" in result.stdout
    mock_session_mgr.start_session.assert_called_once()
    assert mock_session_mgr.start_session.call_args[1]["detached"] == True

@patch("agents.cli.session_manager")
def test_cli_list(mock_session_mgr):
    mock_session_mgr.list_sessions.return_value = [
        {"name": "agent-1", "pid": 1001, "status": "running", "start_time": 1700000000},
        {"name": "agent-2", "pid": 1002, "status": "dead", "start_time": 1700000000}
    ]
    
    result = runner.invoke(app, ["list"])
    
    assert result.exit_code == 0
    assert "Active Agent Sessions" in result.stdout
    assert "agent-1" in result.stdout
    assert "1001" in result.stdout
    assert "running" in result.stdout
    assert "agent-2" in result.stdout
    assert "dead" in result.stdout

@patch("agents.cli.session_manager")
def test_cli_stop(mock_session_mgr):
    mock_session_mgr._get_session_path.return_value.exists.return_value = False # Mock path check if needed, but stop_session handles it
    mock_session_mgr.stop_session.return_value = (True, "Stopped successfully")

    result = runner.invoke(app, ["stop", "agent-1"])
    
    assert result.exit_code == 0
    assert "Stopped successfully" in result.stdout
    mock_session_mgr.stop_session.assert_called_with("agent-1")

@patch("agents.cli.subprocess.run")
@patch("agents.cli.session_manager")
def test_cli_logs(mock_session_mgr, mock_run):
    mock_session_mgr.get_log_path.return_value = "agent.log"
    # We need to mock path.exists() too if get_log_path returns a Path object or check happens in CLI
    # CLI: log_path = session_manager.get_log_path(name); if not log_path.exists(): ...
    
    # Wait, get_log_path returns Path object or None. 
    # And CLI checks .exists()
    
    with patch("agents.cli.Path") as MockPath: # Mocking Path is hard.
        # Better: Mock session_manager.get_log_path returning a MagicMock that has .exists() = True
        log_path_mock = MagicMock()
        log_path_mock.exists.return_value = True
        log_path_mock.__str__.return_value = "agent.log"
        mock_session_mgr.get_log_path.return_value = log_path_mock
        
        result = runner.invoke(app, ["logs", "agent-1"])
        
        assert result.exit_code == 0
        assert "Displaying logs for agent-1" in result.stdout
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "tail"
        assert args[-1] == "agent.log"

def test_cli_config_list():
    result = runner.invoke(app, ["config", "list-keys"])
    assert result.exit_code == 0
    assert "Configuration Keys" in result.stdout
    assert "max_iterations" in result.stdout

def test_cli_config_set():
    with patch("agents.config_manager.ConfigManager.set_value") as mock_set:
        result = runner.invoke(app, ["config", "set", "max_iterations", "10"])
        assert result.exit_code == 0
        mock_set.assert_called_with("max_iterations", "10")