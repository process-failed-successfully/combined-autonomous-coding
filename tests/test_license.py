import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.dependencies import DependencyAnalyzer

@pytest.fixture
def temp_project(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==2.0.1\n")
    return tmp_path

def test_get_pypi_license_classifiers(temp_project):
    analyzer = DependencyAnalyzer(temp_project)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "classifiers": [
                "Programming Language :: Python",
                "License :: OSI Approved :: MIT License"
            ],
            "license": "MIT"
        }
    }

    with patch("requests.get", return_value=mock_response):
        lic = analyzer._get_pypi_license("flask")
        assert lic == "MIT License"

def test_get_pypi_license_field(temp_project):
    analyzer = DependencyAnalyzer(temp_project)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "classifiers": [],
            "license": "BSD-3-Clause"
        }
    }

    with patch("requests.get", return_value=mock_response):
        lic = analyzer._get_pypi_license("flask")
        assert lic == "BSD-3-Clause"

def test_check_licenses_allow_list(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = {
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [{"name": "flask", "version": "2.0.1"}]
            }
        ],
        "node": []
    }

    # Mock _get_pypi_license to return MIT
    with patch.object(analyzer, "_get_pypi_license", return_value="MIT"):
        # Case 1: Allowed
        results = analyzer.check_licenses(data, allow_list=["MIT", "Apache-2.0"])
        assert results[0]["status"] == "OK"

        # Case 2: Not Allowed
        results = analyzer.check_licenses(data, allow_list=["Apache-2.0"])
        assert results[0]["status"] == "VIOLATION"
        assert "not in the allowed list" in results[0]["message"]

def test_check_licenses_deny_list(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = {
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [{"name": "flask", "version": "2.0.1"}]
            }
        ],
        "node": []
    }

    with patch.object(analyzer, "_get_pypi_license", return_value="GPL-3.0"):
        # Case 1: Denied
        results = analyzer.check_licenses(data, deny_list=["GPL-3.0"])
        assert results[0]["status"] == "VIOLATION"
        assert "explicitly denied" in results[0]["message"]

        # Case 2: Not Denied
        results = analyzer.check_licenses(data, deny_list=["MIT"])
        assert results[0]["status"] == "OK"

def test_check_licenses_normalization(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = {
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [{"name": "flask", "version": "2.0.1"}]
            }
        ],
        "node": []
    }

    # Mock returns "MIT License", allow list has "MIT"
    with patch.object(analyzer, "_get_pypi_license", return_value="MIT License"):
        results = analyzer.check_licenses(data, allow_list=["MIT"])
        # Should be OK because "MIT License" -> "mit" and "MIT" -> "mit"
        assert results[0]["status"] == "OK"
