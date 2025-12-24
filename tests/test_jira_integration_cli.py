import pytest
from unittest.mock import patch
from typer.testing import CliRunner
from agents.cli import app, prepare_workspace

runner = CliRunner()


@pytest.fixture
def mock_platformdirs(tmp_path):
    with pytest.MonkeyPatch.context() as m:
        m.setattr("platformdirs.user_data_dir", lambda x: str(tmp_path / "data"))
        yield tmp_path


def test_prepare_workspace_clones(mock_platformdirs, tmp_path):
    # Create fake repo
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    with patch("subprocess.run") as mock_run:
        ws = prepare_workspace("test-jira", repo)

        assert ws == tmp_path / "data" / "workspaces" / "test-jira"
        assert mock_run.called
        assert mock_run.call_args[0][0] == ["git", "clone", str(repo), str(ws)]


def test_run_jira_mode(mock_platformdirs, tmp_path):
    # Fix module-level session_manager path
    from agents.cli import session_manager
    session_manager.data_dir = tmp_path / "data" / "sessions"
    session_manager.logs_dir = tmp_path / "logs"
    session_manager.data_dir.mkdir(parents=True, exist_ok=True)

    # Mock prepare_workspace to return a temp path without actual cloning
    ws_path = tmp_path / "data" / "workspaces" / "test-jira-run"
    ws_path.mkdir(parents=True, exist_ok=True)

    with patch("agents.cli.prepare_workspace", return_value=ws_path) as mock_prep:
        # We need start_session to actually create the file because run() reads it
        # So we don't mock start_session completely, or we mock it to do the right thing.
        # But start_session spawns process. We want to avoid spawning.
        # Let's mock subprocess.Popen inside start_session?
        # Or just mock the read/write in run?
        # Easier: Mock start_session but make it write the file.

        def fake_start(*args, **kwargs):
            # Write fake session file
            import json
            name = args[0]
            path = session_manager._get_session_path(name)
            with open(path, "w") as f:
                json.dump({"pid": 123, "log_file": "log.log", "name": name}, f)
            return {"pid": 123, "log_file": "log.log", "name": name}

        with patch("agents.cli.session_manager.start_session", side_effect=fake_start):
            result = runner.invoke(app, ["run", "--jira", "PROJ-123", "--detached", "--name", "test-jira-run", "--skip-checks"])

            if result.exit_code != 0:
                print(result.stdout)
                print(result.exception)

            assert result.exit_code == 0
            mock_prep.assert_called()

            # Verify file updated with workspace
            import json
            path = session_manager._get_session_path("test-jira-run")
            with open(path, "r") as f:
                data = json.load(f)
            assert data["workspace_path"] == str(ws_path)


def test_stop_cleans_workspace(mock_platformdirs, tmp_path):
    # Fix module-level session_manager path
    from agents.cli import session_manager
    session_manager.data_dir = tmp_path / "data" / "sessions"

    # Setup session with workspace
    name = "cleanup-test"
    ws_path = tmp_path / "data" / "workspaces" / name
    ws_path.mkdir(parents=True, exist_ok=True)

    session_file = tmp_path / "data" / "sessions" / f"{name}.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(session_file, "w") as f:
        json.dump({"pid": 99999, "workspace_path": str(ws_path)}, f)

    with patch("agents.cli.session_manager.stop_session", return_value=(True, "Stopped")):
        result = runner.invoke(app, ["stop", name])
        assert result.exit_code == 0
        assert "Cleaned up workspace" in result.stdout
        assert not ws_path.exists()
