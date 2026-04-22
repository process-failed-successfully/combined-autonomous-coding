import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.auto_fix import run_auto_fix_logic

def test_run_auto_fix_creates_directories(tmp_path: Path):
    run_auto_fix_logic(tmp_path)
    assert (tmp_path / "agents/logs").is_dir()
    assert (tmp_path / "agents/archives").is_dir()
    assert (tmp_path / ".agent_trash").is_dir()

def test_run_auto_fix_fixes_permissions(tmp_path: Path):
    test_script = tmp_path / "run_tests.sh"
    test_script.write_text("#!/bin/bash\necho test\n")
    os.chmod(test_script, stat.S_IRUSR | stat.S_IWUSR)
    assert not bool(os.stat(test_script).st_mode & stat.S_IXUSR)

    run_auto_fix_logic(tmp_path)
    assert bool(os.stat(test_script).st_mode & stat.S_IXUSR)

def test_run_auto_fix_creates_configs(tmp_path: Path):
    run_auto_fix_logic(tmp_path)

    config_file = tmp_path / "agent_config.yaml"
    assert config_file.exists()
    assert "model: gemini-1.5-pro" in config_file.read_text()

    gitignore_file = tmp_path / ".gitignore"
    assert gitignore_file.exists()
    content = gitignore_file.read_text()
    assert "agents/logs/" in content
    assert ".env" in content

@patch("subprocess.run")
def test_run_auto_fix_initializes_git(mock_run, tmp_path: Path):
    run_auto_fix_logic(tmp_path)
    mock_run.assert_called_once_with(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

@patch("subprocess.run")
def test_run_auto_fix_skips_git_init_if_exists(mock_run, tmp_path: Path):
    (tmp_path / ".git").mkdir()
    run_auto_fix_logic(tmp_path)
    mock_run.assert_not_called()
