import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
from agents.pre_flight import PreFlightCheck

@pytest.fixture
def pre_flight(tmp_path):
    # Patch platformdirs to use tmp_path
    with pytest.MonkeyPatch.context() as m:
        m.setattr("platformdirs.user_data_dir", lambda x: str(tmp_path / "data"))
        m.setattr("platformdirs.user_log_dir", lambda x: str(tmp_path / "logs"))
        yield PreFlightCheck()

def test_check_directories_creates_dirs(pre_flight, tmp_path):
    assert pre_flight.check_and_fix_directories()
    assert (tmp_path / "data" / "sessions").exists()
    assert (tmp_path / "logs").exists()

def test_check_workspace_clean_dirty(pre_flight):
    # Mock subprocess to return dirty status
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "M file.txt"
        mock_run.return_value.returncode = 0
        
        # Should return True but print warning
        assert pre_flight.check_workspace_clean()

def test_check_workspace_clean_error(pre_flight):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Git error")
        assert not pre_flight.check_workspace_clean()

def test_run_checks_failure(pre_flight):
    # Mock docker to fail
    with patch("docker.from_env") as mock_docker:
        mock_docker.side_effect = Exception("No docker")
        
        # Should fail
        assert not pre_flight.run_checks()
