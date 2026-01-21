import pytest
from unittest.mock import patch
import json
from shared.health import run_health_check


@pytest.fixture
def mock_dependencies():
    with patch("shared.health.run_tests") as mock_tests, \
         patch("shared.health.run_lint") as mock_lint, \
         patch("shared.health.analyze_project_complexity") as mock_complexity, \
         patch("shared.health.SecurityAuditor") as MockAuditor, \
         patch("shared.health.DependencyAnalyzer") as MockDepAnalyzer:

        # Setup returns
        mock_tests.return_value = {"success": True}
        mock_lint.return_value = {"success": True}
        mock_complexity.return_value = [{"complexity": 5}, {"complexity": 8}]

        mock_auditor = MockAuditor.return_value
        mock_auditor.run_all.return_value = []

        mock_dep = MockDepAnalyzer.return_value
        mock_dep.scan.return_value = {"python": []}
        mock_dep.check_updates.return_value = {"python": []}

        yield


def test_health_report_html_generation(tmp_path, mock_dependencies):
    output_file = tmp_path / "report.html"

    # Run health check
    run_health_check(tmp_path, output_format="html", output_file=str(output_file))

    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    assert "<!DOCTYPE html>" in content
    assert "Project Health Report" in content
    assert "Overall Score" in content


def test_health_report_json_generation(tmp_path, mock_dependencies):
    output_file = tmp_path / "report.json"

    # Run health check
    run_health_check(tmp_path, output_format="json", output_file=str(output_file))

    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    data = json.loads(content)

    assert "score" in data
    assert "grade" in data
    assert "metrics" in data
    assert "timestamp" in data


def test_health_report_default_path(tmp_path, mock_dependencies):
    # Run health check without explicit output file
    run_health_check(tmp_path, output_format="html")

    expected_file = tmp_path / "health_report.html"
    assert expected_file.exists()
