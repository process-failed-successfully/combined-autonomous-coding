from unittest.mock import MagicMock, patch
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
    assert "pause" in result.stdout
    assert "resume" in result.stdout
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
    assert args[0][0] == "test-agent"  # name
    assert args[1]["detached"] is False


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
    assert mock_session_mgr.start_session.call_args[1]["detached"] is True


@patch("agents.cli.session_manager")
def test_cli_list(mock_session_mgr):
    mock_session_mgr.list_sessions.return_value = [
        {"name": "agent-1", "pid": 1001, "status": "running", "start_time": 1700000000},
        {"name": "agent-2", "pid": 1002, "status": "dead", "start_time": 1700000000},
        {"name": "agent-3", "pid": 1003, "status": "paused", "start_time": 1700000000}
    ]

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Active Agent Sessions" in result.stdout
    assert "agent-1" in result.stdout
    assert "1001" in result.stdout
    assert "running" in result.stdout
    assert "agent-2" in result.stdout
    assert "dead" in result.stdout
    assert "agent-3" in result.stdout
    assert "paused" in result.stdout


@patch("agents.cli.session_manager")
def test_cli_pause(mock_session_mgr):
    mock_session_mgr.pause_session.return_value = (True, "Session paused successfully.")

    result = runner.invoke(app, ["pause", "agent-1"])

    assert result.exit_code == 0
    assert "Session paused successfully." in result.stdout
    mock_session_mgr.pause_session.assert_called_with("agent-1")


@patch("agents.cli.session_manager")
def test_cli_resume(mock_session_mgr):
    mock_session_mgr.resume_session.return_value = (True, "Session resumed successfully.")

    result = runner.invoke(app, ["resume", "agent-1"])

    assert result.exit_code == 0
    assert "Session resumed successfully." in result.stdout
    mock_session_mgr.resume_session.assert_called_with("agent-1")


@patch("agents.cli.session_manager")
def test_cli_stop(mock_session_mgr):
    mock_session_mgr._get_session_path.return_value.exists.return_value = False  # Mock path check
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

    # Correct way to mock a method that returns a Path object
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.configure_mock(**{"__str__.return_value": "agent.log"})
    mock_session_mgr.get_log_path.return_value = mock_path_instance

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


@patch("agents.cli.session_manager")
def test_cli_prune_no_force(mock_session_mgr):
    mock_session_mgr.prune_sessions.return_value = ["dead-session"]
    result = runner.invoke(app, ["prune"])

    assert result.exit_code == 0
    assert "Pruning dead sessions..." in result.stdout
    assert "Successfully pruned 1 session" in result.stdout
    assert "dead-session" in result.stdout
    mock_session_mgr.prune_sessions.assert_called_once_with(force=False)


@patch("agents.cli.session_manager")
def test_cli_prune_force(mock_session_mgr):
    mock_session_mgr.prune_sessions.return_value = ["live-session", "dead-session"]
    result = runner.invoke(app, ["prune", "--force"])

    assert result.exit_code == 0
    assert "--force will also stop and remove currently running sessions" in result.stdout
    assert "Pruning all sessions..." in result.stdout
    assert "Successfully pruned 2 session" in result.stdout
    assert "live-session" in result.stdout
    mock_session_mgr.prune_sessions.assert_called_once_with(force=True)


@patch("agents.cli.session_manager")
def test_cli_prune_empty(mock_session_mgr):
    mock_session_mgr.prune_sessions.return_value = []
    result = runner.invoke(app, ["prune"])

    assert result.exit_code == 0
    assert "No sessions found to prune" in result.stdout
    mock_session_mgr.prune_sessions.assert_called_once_with(force=False)


def test_session_manager_prune_logic(tmp_path):
    from agents.session_manager import SessionManager
    from pathlib import Path
    import json

    # Create a real SessionManager but point it to tmp_path
    sm = SessionManager()
    sm.data_dir = tmp_path / "sessions"
    sm.logs_dir = tmp_path / "logs"
    sm.data_dir.mkdir(parents=True)
    sm.logs_dir.mkdir(parents=True)

    # Create mock session files
    live_session = {
        "name": "live-session",
        "pid": 9999999,  # Highly unlikely to exist
        "status": "running",
        "log_file": str(sm.logs_dir / "live.log"),
        "workspace_path": str(tmp_path / "live_workspace")
    }

    dead_session = {
        "name": "dead-session",
        "pid": 9999998,
        "status": "dead",
        "log_file": str(sm.logs_dir / "dead.log"),
        "workspace_path": str(tmp_path / "dead_workspace")
    }

    # We will mock _get_process_status instead of relying on pid lookup
    with patch.object(sm, "_get_process_status") as mock_get_process_status:
        def side_effect(pid):
            if pid == 9999999:
                return "running"
            if pid == 9999998:
                return "dead"
            return "dead"
        mock_get_process_status.side_effect = side_effect

        # Write config files
        (sm.data_dir / "live-session.json").write_text(json.dumps(live_session))
        (sm.data_dir / "dead-session.json").write_text(json.dumps(dead_session))

        # Create log files
        Path(live_session["log_file"]).touch()
        Path(dead_session["log_file"]).touch()

        # Create workspaces
        Path(live_session["workspace_path"]).mkdir()
        Path(dead_session["workspace_path"]).mkdir()

        # Prune with force=False
        pruned = sm.prune_sessions(force=False)
        assert "dead-session" in pruned
        assert "live-session" not in pruned

        # Check files
        assert (sm.data_dir / "live-session.json").exists()
        assert not (sm.data_dir / "dead-session.json").exists()

        assert Path(live_session["log_file"]).exists()
        assert not Path(dead_session["log_file"]).exists()

        assert Path(live_session["workspace_path"]).exists()
        assert not Path(dead_session["workspace_path"]).exists()

        # Prune with force=True
        # We need to mock stop_session since it tries to kill the process
        with patch.object(sm, "stop_session") as mock_stop:
            pruned2 = sm.prune_sessions(force=True)
            assert "live-session" in pruned2
            mock_stop.assert_called_once_with("live-session")


@patch("agents.cli.session_manager")
def test_cli_list_empty(mock_session_mgr):
    mock_session_mgr.list_sessions.return_value = []
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No active sessions found" in result.stdout
