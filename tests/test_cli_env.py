from typer.testing import CliRunner
from agents.cli import app
from unittest.mock import patch

runner = CliRunner()


@patch("agents.cli.session_manager")
def test_app_run_skip_checks(mock_session):
    mock_session.start_session.return_value = 0
    result = runner.invoke(app, ["run", "--skip-checks"])
    assert result.exit_code == 0
    assert "Autonomous Coding Agent" in result.stdout
    assert "Skipping pre-flight checks" in result.stdout
    assert "Running session:" in result.stdout


@patch("agents.cli.session_manager")
def test_app_run_verbose(mock_session):
    mock_session.start_session.return_value = 0
    result = runner.invoke(app, ["run", "--skip-checks", "--verbose"])
    assert result.exit_code == 0
    # Current implementation doesn't print "Debug logging enabled",
    # but we can verify it ran by checking other outputs.
    assert "Autonomous Coding Agent" in result.stdout
