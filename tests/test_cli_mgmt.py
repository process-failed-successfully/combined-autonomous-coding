import pytest
from typer.testing import CliRunner
from agents.cli import app

runner = CliRunner()


@pytest.fixture
def clean_sessions(tmp_path):
    # Setup mock paths again for the CLI which imports session_manager
    # This is tricky because agents.cli imports session_manager at module level.
    # We might need to patch SessionManager class in agents.cli
    pass

# Since patching module-level globals is hard, let's just rely on mocked platformdirs
# if we can, or just accept it writes to real dirs in the container.
# BUT, we are in a container, so writing to ~/.local/share is fine,
# provided we clean up.


def test_cli_detached_flow():
    # 1. Run detached
    result = runner.invoke(app, ["run", "--detached", "--name", "cli-test", "--skip-checks"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Launching detached session: cli-test" in result.stdout
    assert "Session started!" in result.stdout

    # 2. List
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "cli-test" in result.stdout
    assert "running" in result.stdout

    # 3. Stop
    result = runner.invoke(app, ["stop", "cli-test"])
    assert result.exit_code == 0
    assert "Stopped" in result.stdout

    # 4. List again (should be empty)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "cli-test" not in result.stdout


def test_cli_logs():
    # Start one
    runner.invoke(app, ["run", "--detached", "--name", "log-test", "--skip-checks"])

    # Check logs
    result = runner.invoke(app, ["logs", "log-test"])
    assert result.exit_code == 0
    assert "Displaying logs for log-test" in result.stdout

    # Check attach
    # Attach uses tail -f which blocks. We can't easily test blocking commands with invoke
    # unless we mock subprocess.run to not block or use timeout.
    # But for now, let's just ensure it calls logs.

    runner.invoke(app, ["stop", "log-test"])
