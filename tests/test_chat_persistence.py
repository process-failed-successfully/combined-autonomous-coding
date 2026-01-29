import shutil
import tempfile
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Mock rich before importing shared.chat
sys.modules["rich"] = MagicMock()
sys.modules["rich.console"] = MagicMock()
sys.modules["rich.prompt"] = MagicMock()
sys.modules["rich.markdown"] = MagicMock()

# Now import
from shared.chat import ChatManager
from shared.work_session import WorkSessionManager

@pytest.fixture
def temp_project():
    temp_dir = Path(tempfile.mkdtemp())
    (temp_dir / ".git").mkdir() # Mock git repo
    (temp_dir / ".agent_sessions").mkdir(parents=True, exist_ok=True) # Ensure sessions dir exists
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_chat_manager_loads_session_history(temp_project):
    # Setup: Create a session with history
    session_manager = WorkSessionManager(temp_project)
    session_manager.create("test-session")
    session_manager.add_chat_turn("test-session", "user", "Hello from history")
    session_manager.add_chat_turn("test-session", "agent", "Hi from history")

    # Init ChatManager
    # We need to mock the agent to avoid actual calls
    with patch("shared.chat.ChatManager._init_agent") as mock_init_agent, \
         patch("shared.chat.WorkSessionManager.get_active_session") as mock_get_active:

        mock_agent = MagicMock()
        mock_init_agent.return_value = mock_agent

        # Ensure it sees the active session
        mock_get_active.return_value = session_manager.load_session("test-session")

        # Manually force the session manager to use the temp project dir
        # (Since ChatManager initializes its own WorkSessionManager)
        with patch("shared.chat.WorkSessionManager") as MockWSM:
            MockWSM.return_value = session_manager

            manager = ChatManager(temp_project, agent_type="gemini", verbose=False)

            # Assert history is loaded
            assert len(manager.session.history) == 2
            assert manager.session.history[0].role == "user"
            assert manager.session.history[0].content == "Hello from history"
            assert manager.session.history[1].role == "agent"
            assert manager.session.history[1].content == "Hi from history"

@pytest.mark.asyncio
async def test_chat_manager_saves_session_history(temp_project):
    # Setup: Create active session
    session_manager = WorkSessionManager(temp_project)
    session_manager.create("active-session")

    # Init ChatManager and mock agent/console/prompt
    with patch("shared.chat.ChatManager._init_agent") as mock_init_agent, \
         patch("shared.chat.Prompt.ask") as mock_prompt, \
         patch("shared.chat.WorkSessionManager") as MockWSM:

        # Make ChatManager use our session manager instance
        MockWSM.return_value = session_manager

        # Use AsyncMock for the agent
        mock_agent = AsyncMock()
        # Mock run_agent_session to return success
        mock_agent.run_agent_session.return_value = (True, "I am an agent", [])
        mock_init_agent.return_value = mock_agent

        # Mock user input sequence: "Hello", then "/exit"
        mock_prompt.side_effect = ["Hello", "/exit"]

        manager = ChatManager(temp_project, agent_type="gemini", verbose=False)
        # Mock console print to avoid clutter
        manager.console = MagicMock()

        # Run chat loop
        await manager.run()

        # Assert session file has updated history
        session = session_manager.load_session("active-session")
        assert len(session.chat_history) == 2
        assert session.chat_history[0] == {"role": "user", "content": "Hello"}
        assert session.chat_history[1] == {"role": "agent", "content": "I am an agent"}
