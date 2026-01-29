import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.chat import ChatSession, ChatManager

class TestChatSession(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

        # Create a dummy file
        self.test_file = self.project_dir / "test.txt"
        self.test_file.write_text("Hello World", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_remove_file(self):
        session = ChatSession(self.project_dir)

        # Add file
        success = session.add_file("test.txt")
        self.assertTrue(success)
        self.assertIn("test.txt", session.files_context)
        self.assertEqual(session.files_context["test.txt"], "Hello World")

        # Add non-existent file
        success = session.add_file("nonexistent.txt")
        self.assertFalse(success)

        # Remove file
        success = session.remove_file("test.txt")
        self.assertTrue(success)
        self.assertNotIn("test.txt", session.files_context)

        # Remove non-existent file from context
        success = session.remove_file("nonexistent.txt")
        self.assertFalse(success)

    def test_history(self):
        session = ChatSession(self.project_dir)
        session.add_turn("user", "Hello")
        session.add_turn("agent", "Hi there")

        self.assertEqual(len(session.history), 2)
        self.assertEqual(session.history[0].role, "user")
        self.assertEqual(session.history[0].content, "Hello")

        session.clear_history()
        self.assertEqual(len(session.history), 0)

class TestChatManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("shared.chat.GeminiAgent")
    @patch("shared.chat.Console")
    async def test_chat_flow(self, MockConsole, MockGeminiAgent):
        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("continue", "I am an agent", [])
        MockGeminiAgent.return_value = mock_agent

        # Initialize Manager
        manager = ChatManager(self.project_dir, agent_type="gemini")

        # Test Prompt Building
        manager.session.add_turn("user", "Previous input")
        manager.session.add_turn("agent", "Previous response")

        prompt = manager._build_prompt("Current input")
        self.assertIn("Previous input", prompt)
        self.assertIn("Previous response", prompt)
        self.assertIn("Current input", prompt)

        # Test Command Handling
        res = await manager._handle_command("/clear")
        self.assertTrue(res)
        self.assertEqual(len(manager.session.history), 0)

        res = await manager._handle_command("/unknown")
        self.assertTrue(res) # Should handled but print error

if __name__ == "__main__":
    unittest.main()
