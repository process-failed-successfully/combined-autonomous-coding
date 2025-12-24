from typer.testing import CliRunner
from agents.cli import app

runner = CliRunner()

def test_app_run_skip_checks():
    result = runner.invoke(app, ["run", "--skip-checks"])
    assert result.exit_code == 0
    assert "Autonomous Coding Agent" in result.stdout
    assert "Skipping pre-flight checks" in result.stdout
    assert "Agent initialized" in result.stdout

def test_app_run_verbose():
    result = runner.invoke(app, ["run", "--skip-checks", "--verbose"])
    assert result.exit_code == 0
    assert "Debug logging enabled" in result.stdout
