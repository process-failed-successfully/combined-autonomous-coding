from typer.testing import CliRunner
from agents.cli import app
from unittest.mock import patch

runner = CliRunner()


def test_cli_run_dry():
    # Mock pre-flight checks to pass
    with patch("agents.cli.PreFlightCheck") as MockCheck:
        instance = MockCheck.return_value
        instance.run_checks.return_value = True

        result = runner.invoke(app, ["run"])

        print(f"Exit Code: {result.exit_code}")
        print(f"Output:\n{result.stdout}")

        assert result.exit_code == 0
        assert "Autonomous Coding Agent" in result.stdout
        assert "Checks passed!" in result.stdout
        assert "Mode: Autonomous" in result.stdout


if __name__ == "__main__":
    test_cli_run_dry()
