import os
import signal
import pytest
from agents.session_manager import SessionManager


@pytest.fixture
def session_manager(tmp_path):
    # Patch platformdirs to use tmp_path
    with pytest.MonkeyPatch.context() as m:
        m.setattr("platformdirs.user_data_dir", lambda x: str(tmp_path / "data"))
        m.setattr("platformdirs.user_log_dir", lambda x: str(tmp_path / "logs"))
        yield SessionManager()


def test_start_session_detached(session_manager):
    cmd = ["sleep", "10"]
    name = "test-session"

    session = session_manager.start_session(name, cmd, detached=True)

    assert session["name"] == name
    assert session["pid"] > 0
    assert session["type"] == "detached"
    assert os.path.exists(session["log_file"])
    assert session_manager._get_session_path(name).exists()

    # Clean up
    os.kill(session["pid"], signal.SIGKILL)


def test_list_sessions(session_manager):
    cmd = ["sleep", "10"]
    session_manager.start_session("s1", cmd, detached=True)

    sessions = session_manager.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["name"] == "s1"
    assert sessions[0]["status"] == "running"

    # Kill it
    os.kill(sessions[0]["pid"], signal.SIGKILL)
    # Wait for OS to register death (conceptually, though _is_process_running checks immediately)

    # Should show as dead or be cleaned up?
    # list_sessions marks as dead but returns it.
    sessions = session_manager.list_sessions()
    # It might still return running if PID reused or race condition, but usually OK.

    # Stop session
    session_manager.stop_session("s1")
    assert len(session_manager.list_sessions()) == 0


def test_stop_session(session_manager):
    cmd = ["sleep", "10"]
    session = session_manager.start_session("s2", cmd, detached=True)

    pid = session["pid"]
    assert session_manager._is_process_running(pid)

    success, msg = session_manager.stop_session("s2")
    assert success
    assert not session_manager._is_process_running(pid)
    assert not session_manager._get_session_path("s2").exists()


def test_start_duplicate_session(session_manager):
    cmd = ["sleep", "10"]
    session_manager.start_session("s3", cmd, detached=True)

    with pytest.raises(ValueError):
        session_manager.start_session("s3", cmd, detached=True)

    session_manager.stop_session("s3")
