from typer.testing import CliRunner
from agents.cli import app
from unittest.mock import patch, MagicMock

runner = CliRunner()


def test_app_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Autonomous Coding Agent CLI Launcher" in result.stdout.replace("\n", " ")


@patch("agents.cli.session_manager")
@patch("agents.cli.PreFlightCheck")
def test_run_command_success(mock_check_cls, mock_session):
    mock_check = MagicMock()
    mock_check.run_checks.return_value = True
    mock_check_cls.return_value = mock_check
    mock_session.start_session.return_value = 0

    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "Checks passed!" in result.stdout
    assert "Running session:" in result.stdout


@patch("agents.cli.PreFlightCheck")
def test_run_command_fail_checks(mock_check_cls):
    mock_check = MagicMock()
    mock_check.run_checks.return_value = False
    mock_check_cls.return_value = mock_check

    result = runner.invoke(app, ["run"])
    assert result.exit_code == 1
    assert "Pre-flight checks failed" in result.stdout


@patch("agents.cli.session_manager")
def test_run_skip_checks(mock_session):
    mock_session.start_session.return_value = 0
    result = runner.invoke(app, ["run", "--skip-checks"])
    assert result.exit_code == 0
    assert "Skipping pre-flight checks" in result.stdout


def test_config_list_keys():
    result = runner.invoke(app, ["config", "list-keys"])
    assert result.exit_code == 0
    assert "Configuration Keys" in result.stdout


def test_config_set():
    # We mock ConfigManager to avoid writing to actual files during test
    with patch("agents.cli.ConfigManager") as mock_cm_cls:
        mock_cm = MagicMock()
        mock_cm_cls.return_value = mock_cm

        result = runner.invoke(app, ["config", "set", "max_iterations", "100"])
        assert result.exit_code == 0
        mock_cm.set_value.assert_called_with("max_iterations", "100")
