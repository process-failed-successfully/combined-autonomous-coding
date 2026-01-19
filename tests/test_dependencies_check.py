import pytest
from unittest.mock import patch, MagicMock
from shared.dependencies import DependencyAnalyzer


@pytest.fixture
def temp_project(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==2.0.1\n")
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^17.0.2"}}')
    return tmp_path


def test_check_updates(temp_project):
    analyzer = DependencyAnalyzer(temp_project)

    # Mock data to simulate scan() result
    data = {
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [{"name": "flask", "version": "==2.0.1"}]
            }
        ],
        "node": [
            {
                "source": "package.json",
                "dependencies": [{"name": "react", "version": "^17.0.2"}]
            }
        ]
    }

    # Mock requests.get
    with patch("requests.get") as mock_get:
        # Setup mock responses
        def side_effect(url, timeout=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200

            if "pypi.org" in url and "flask" in url:
                mock_resp.json.return_value = {"info": {"version": "3.0.0"}}
            elif "registry.npmjs.org" in url and "react" in url:
                mock_resp.json.return_value = {"version": "18.0.0"}
            else:
                mock_resp.status_code = 404
            return mock_resp

        mock_get.side_effect = side_effect

        updated_data = analyzer.check_updates(data)

        # Python checks
        flask_dep = updated_data["python"][0]["dependencies"][0]
        assert flask_dep["latest"] == "3.0.0"
        assert flask_dep["outdated"] is True

        # Node checks
        react_dep = updated_data["node"][0]["dependencies"][0]
        assert react_dep["latest"] == "18.0.0"
        assert react_dep["outdated"] is True


def test_check_updates_up_to_date(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = {
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [{"name": "flask", "version": "==2.0.1"}]
            }
        ],
        "node": []
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"info": {"version": "2.0.1"}}
        mock_get.return_value = mock_resp

        updated_data = analyzer.check_updates(data)
        flask_dep = updated_data["python"][0]["dependencies"][0]
        assert flask_dep["latest"] == "2.0.1"
        assert flask_dep["outdated"] is False


def test_generate_updates_table(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = {
        "python": [
            {
                "dependencies": [
                    {"name": "flask", "version": "==2.0.1", "latest": "3.0.0", "outdated": True},
                    {"name": "requests", "version": "==2.26.0", "latest": "2.26.0", "outdated": False}
                ]
            }
        ],
        "node": []
    }

    table = analyzer.generate_updates_table(data)
    assert "flask" in table
    assert "3.0.0" in table
    assert "requests" not in table  # Only outdated ones shown in list
