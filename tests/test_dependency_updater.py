import sys
from unittest.mock import patch

import pytest

from shared.dependencies import DependencyUpdater


@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project directory."""
    # requirements.txt
    (tmp_path / "requirements.txt").write_text(
        "flask==2.0.1\nrequests>=2.25.1\n# comment\nnumpy\n"
    )

    # package.json
    (tmp_path / "package.json").write_text("{}")

    return tmp_path


def test_update_python_requirement_exact(temp_project):
    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    # Test updating flask (exact match)
    success = updater.update_dependency(req_file, "flask", "3.0.0")
    assert success

    content = req_file.read_text()
    assert "flask==3.0.0" in content
    assert "flask==2.0.1" not in content


def test_update_python_requirement_ge(temp_project):
    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    # Test updating requests (>=)
    success = updater.update_dependency(req_file, "requests", "2.31.0")
    assert success

    content = req_file.read_text()
    assert "requests==2.31.0" in content
    assert "requests>=2.25.1" not in content


def test_update_python_requirement_plain(temp_project):
    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    # Test updating numpy (no version)
    success = updater.update_dependency(req_file, "numpy", "1.26.0")
    assert success

    content = req_file.read_text()
    assert "numpy==1.26.0" in content


def test_update_python_requirement_case_insensitive(temp_project):
    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    # Test updating FLASK (case insensitive match)
    success = updater.update_dependency(req_file, "FLASK", "3.0.0")
    assert success

    content = req_file.read_text()
    # It should preserve the original case "flask"
    assert "flask==3.0.0" in content


def test_update_python_requirement_not_found(temp_project):
    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    # Test updating non-existent package
    success = updater.update_dependency(req_file, "missing-package", "1.0.0")
    assert not success

    content = req_file.read_text()
    assert "missing-package" not in content


@patch("shared.dependencies.shutil.which")
@patch("shared.dependencies.subprocess.run")
def test_update_node_package_npm(mock_run, mock_which, temp_project):
    updater = DependencyUpdater(temp_project)
    pkg_file = temp_project / "package.json"

    # Mock npm existence
    def which_side_effect(cmd):
        if cmd == "npm":
            return "/usr/bin/npm"
        return None
    mock_which.side_effect = which_side_effect

    success = updater.update_dependency(pkg_file, "react", "18.0.0")
    assert success

    mock_run.assert_called_with(
        ["npm", "install", "react@18.0.0"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )


@patch("shared.dependencies.shutil.which")
@patch("shared.dependencies.subprocess.run")
def test_update_node_package_yarn(mock_run, mock_which, temp_project):
    updater = DependencyUpdater(temp_project)
    pkg_file = temp_project / "package.json"
    (temp_project / "yarn.lock").touch()

    # Mock yarn existence
    def which_side_effect(cmd):
        if cmd == "yarn":
            return "/usr/bin/yarn"
        return None
    mock_which.side_effect = which_side_effect

    success = updater.update_dependency(pkg_file, "react", "18.0.0")
    assert success

    mock_run.assert_called_with(
        ["yarn", "add", "react@18.0.0"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )


@patch("shared.dependencies.shutil.which")
@patch("shared.dependencies.subprocess.run")
def test_update_node_package_pnpm(mock_run, mock_which, temp_project):
    updater = DependencyUpdater(temp_project)
    pkg_file = temp_project / "package.json"
    (temp_project / "pnpm-lock.yaml").touch()

    # Mock pnpm existence
    def which_side_effect(cmd):
        if cmd == "pnpm":
            return "/usr/bin/pnpm"
        return None
    mock_which.side_effect = which_side_effect

    success = updater.update_dependency(pkg_file, "react", "18.0.0", dep_type="dev")
    assert success

    mock_run.assert_called_with(
        ["pnpm", "add", "--save-dev", "react@18.0.0"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )


@patch("shared.dependencies.shutil.which")
@patch("shared.dependencies.subprocess.run")
def test_add_package_node(mock_run, mock_which, temp_project):
    updater = DependencyUpdater(temp_project)

    # Mock npm
    mock_which.return_value = "/usr/bin/npm"

    success = updater.add_package("axios", version="1.0.0")
    assert success
    mock_run.assert_called_with(
        ["npm", "install", "axios@1.0.0"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )


@patch("shared.dependencies.shutil.which")
@patch("shared.dependencies.subprocess.run")
def test_remove_package_node(mock_run, mock_which, temp_project):
    updater = DependencyUpdater(temp_project)

    # Mock npm
    mock_which.return_value = "/usr/bin/npm"

    success = updater.remove_package("axios")
    assert success
    mock_run.assert_called_with(
        ["npm", "uninstall", "axios"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )


@patch("shared.dependencies.subprocess.run")
def test_add_package_python(mock_run, temp_project):
    # Remove package.json so it falls back to Python
    (temp_project / "package.json").unlink()

    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    success = updater.add_package("pandas", version="2.0.0")
    assert success

    # Check pip install called
    mock_run.assert_called_with(
        [sys.executable, "-m", "pip", "install", "pandas==2.0.0"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )

    # Check requirements.txt updated
    content = req_file.read_text()
    assert "pandas==2.0.0" in content


@patch("shared.dependencies.subprocess.run")
def test_remove_package_python(mock_run, temp_project):
    # Remove package.json so it falls back to Python
    (temp_project / "package.json").unlink()

    updater = DependencyUpdater(temp_project)
    req_file = temp_project / "requirements.txt"

    success = updater.remove_package("flask")  # flask is in temp_project fixture
    assert success

    # Check pip uninstall called
    mock_run.assert_called_with(
        [sys.executable, "-m", "pip", "uninstall", "-y", "flask"],
        cwd=temp_project,
        check=True,
        capture_output=True
    )

    # Check requirements.txt updated
    content = req_file.read_text()
    assert "flask" not in content
