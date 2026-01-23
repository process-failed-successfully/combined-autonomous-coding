import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile
import json
from dataclasses import dataclass

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DataTable, RichLog, Input, ListView
from shared.tui import AgentTUI, SessionTab
from shared.work_session import Session

class TestTUISession(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock WorkSessionManager
        self.patcher_manager = patch("shared.tui.WorkSessionManager")
        self.mock_manager_cls = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_cls.return_value

    def tearDown(self):
        self.patcher_manager.stop()
        shutil.rmtree(self.test_dir)

    async def test_session_tab_structure(self):
        """Test the session tab structure."""
        # We need to patch SessionTab because we haven't modified AgentTUI yet
        # But wait, I can just instantiate SessionTab directly
        tab = SessionTab(self.project_dir)
        self.assertIsNotNone(tab)

    async def test_load_sessions(self):
        """Test loading sessions into the table."""
        self.mock_manager.list_sessions.return_value = [
            {"name": "session1", "updated_at": "2023-01-01T12:00:00", "description": "Desc 1"},
            {"name": "session2", "updated_at": "2023-01-02T12:00:00", "description": "Desc 2"}
        ]
        self.mock_manager.get_active_session.return_value = Session(
            name="session1", created_at="", updated_at="", files=[], notes=[]
        )

        tab = SessionTab(self.project_dir)
        tab.notify = MagicMock()

        mock_table = MagicMock(spec=DataTable)
        tab.query_one = MagicMock(return_value=mock_table)

        tab.load_sessions()

        self.mock_manager.list_sessions.assert_called_once()
        self.assertEqual(mock_table.add_row.call_count, 2)

        # Check if active session is marked
        # We can't easily check the rendered string formatting here without strict coupling
        # but we can verify the data passed
        args1 = mock_table.add_row.call_args_list[0][0]
        self.assertIn("session1", str(args1)) # Should be marked or present

    async def test_create_session(self):
        """Test creating a new session."""
        tab = SessionTab(self.project_dir)
        tab.notify = MagicMock()
        tab.load_sessions = MagicMock()

        mock_input = MagicMock(spec=Input)
        mock_input.value = "new_session"

        tab.query_one = MagicMock(return_value=mock_input)

        # Simulate creating session
        await tab.create_session()

        self.mock_manager.create.assert_called_with("new_session")
        tab.load_sessions.assert_called()
        self.assertEqual(mock_input.value, "") # Should be cleared

    async def test_select_session(self):
        """Test selecting a session to view details."""
        tab = SessionTab(self.project_dir)
        tab.notify = MagicMock()

        session_data = Session(
            name="session1",
            created_at="2023-01-01",
            updated_at="2023-01-02",
            files=["file1.py"],
            notes=["Note 1"]
        )
        self.mock_manager.load_session.return_value = session_data

        # Mock UI elements
        mock_details_log = MagicMock(spec=RichLog)
        mock_files_list = MagicMock(spec=ListView)
        mock_notes_log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if "#session-details-log" in selector: return mock_details_log
            if "#session-files-list" in selector: return mock_files_list
            if "#session-notes-log" in selector: return mock_notes_log
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        # Simulate selection
        tab.load_session_details("session1")

        self.mock_manager.load_session.assert_called_with("session1")
        # mock_details_log is not used in the implementation for writing, header uses update()
        mock_files_list.clear.assert_called()
        mock_notes_log.write.assert_called()
