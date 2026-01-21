import shutil
import tempfile
from pathlib import Path
import pytest
from shared.work_session import WorkSessionManager

@pytest.fixture
def temp_project():
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_create_session(temp_project):
    manager = WorkSessionManager(temp_project)
    session = manager.create("test-session", "Test Description")

    assert session.name == "test-session"
    assert session.description == "Test Description"
    assert (temp_project / ".agent_sessions" / "test-session.json").exists()
    assert (temp_project / ".agent_sessions" / "active_session.txt").read_text() == "test-session"

def test_load_session(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("session1")

    loaded = manager.load_session("session1")
    assert loaded is not None
    assert loaded.name == "session1"

    assert manager.load_session("non-existent") is None

def test_list_sessions(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("session1")
    manager.create("session2")

    sessions = manager.list_sessions()
    assert len(sessions) == 2
    names = sorted([s["name"] for s in sessions])
    assert names == ["session1", "session2"]

def test_active_session_management(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("s1")
    assert manager.get_active_session().name == "s1"

    manager.create("s2")
    assert manager.get_active_session().name == "s2"

    manager.set_active_session("s1")
    assert manager.get_active_session().name == "s1"

    manager.stop_session()
    assert manager.get_active_session() is None

def test_file_management(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("s1")

    # Create dummy file
    (temp_project / "file.py").touch()

    manager.add_file("s1", "file.py")
    session = manager.load_session("s1")
    assert "file.py" in session.files

    manager.remove_file("s1", "file.py")
    session = manager.load_session("s1")
    assert "file.py" not in session.files

def test_note_management(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("s1")

    manager.add_note("s1", "This is a note")
    session = manager.load_session("s1")
    assert len(session.notes) == 1
    assert "This is a note" in session.notes[0]

def test_delete_session(temp_project):
    manager = WorkSessionManager(temp_project)
    manager.create("s1")
    assert manager.get_active_session().name == "s1"

    manager.delete_session("s1")
    assert not (temp_project / ".agent_sessions" / "s1.json").exists()
    assert manager.get_active_session() is None
