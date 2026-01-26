import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil

from shared.chat import ChatSession

class TestChatSession(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.session = ChatSession(self.test_dir, agent_type="gemini")
        # Mock the agent to prevent real API calls
        self.session.agent = AsyncMock()
        self.session.console = MagicMock() # Mock console to avoid output

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        self.assertEqual(self.session.project_dir, self.test_dir)
        self.assertEqual(self.session.agent_type, "gemini")
        self.assertEqual(self.session.history, [])
        self.assertEqual(self.session.context_files, [])

    def test_add_messages(self):
        self.session.add_user_message("Hello")
        self.assertEqual(len(self.session.history), 1)
        self.assertEqual(self.session.history[0], {"role": "user", "content": "Hello"})

        self.session.add_agent_message("Hi there")
        self.assertEqual(len(self.session.history), 2)
        self.assertEqual(self.session.history[1], {"role": "agent", "content": "Hi there"})

    def test_add_context_file(self):
        test_file = self.test_dir / "test.txt"
        test_file.write_text("content")

        self.session.add_context_file("test.txt")
        self.assertIn(test_file, self.session.context_files)

        # Test adding non-existent file
        self.session.add_context_file("fake.txt")
        self.assertEqual(len(self.session.context_files), 1) # Should not add

    def test_clear_history(self):
        self.session.add_user_message("test")
        self.session.clear_history()
        self.assertEqual(self.session.history, [])

    def test_save_transcript(self):
        self.session.add_user_message("User says hello")
        self.session.add_agent_message("Agent replies")

        outfile = "transcript.md"
        self.session.save_transcript(outfile)

        transcript_path = self.test_dir / outfile
        self.assertTrue(transcript_path.exists())
        content = transcript_path.read_text()
        self.assertIn("## USER", content)
        self.assertIn("User says hello", content)
        self.assertIn("## AGENT", content)
        self.assertIn("Agent replies", content)

    @patch("shared.chat.get_chat_prompt")
    @patch("shared.chat.get_file_tree")
    async def test_run_turn(self, mock_file_tree, mock_get_prompt):
        mock_get_prompt.return_value = "Prompt: {history} {user_message}"
        mock_file_tree.return_value = "file_tree"

        self.session.agent.run_agent_session.return_value = ("done", "Response", [])

        self.session.add_user_message("My Question")
        await self.session.run_turn()

        # Check if agent was called
        self.assertTrue(self.session.agent.run_agent_session.called)
        call_args = self.session.agent.run_agent_session.call_args[0][0]

        # Check prompt construction
        self.assertIn("Prompt:", call_args)
        self.assertIn("My Question", call_args)
        self.assertIn("(No previous conversation)", call_args) # First turn
        self.assertIn("file_tree", call_args)

        # Check history update
        self.assertEqual(len(self.session.history), 2)
        self.assertEqual(self.session.history[1]["role"], "agent")
        self.assertEqual(self.session.history[1]["content"], "Response")

    @patch("shared.chat.get_chat_prompt")
    @patch("shared.chat.get_file_tree")
    async def test_run_turn_with_history(self, mock_file_tree, mock_get_prompt):
        mock_get_prompt.return_value = "{history}"
        mock_file_tree.return_value = ""
        self.session.agent.run_agent_session.return_value = ("done", "Response", [])

        self.session.add_user_message("Q1")
        self.session.add_agent_message("A1")
        self.session.add_user_message("Q2")

        await self.session.run_turn()

        call_args = self.session.agent.run_agent_session.call_args[0][0]
        self.assertIn("**User**: Q1", call_args)
        self.assertIn("**Agent**: A1", call_args)
        # Q2 is the current user message, so it's injected via {user_message} (which we didn't put in mock prompt but that's fine for this test)
        # Actually I replaced {history} with history_text.

        # Ensure we don't have Q2 in the history text part (it's the 'current' message)
        self.assertNotIn("**User**: Q2", call_args)

if __name__ == "__main__":
    unittest.main()
