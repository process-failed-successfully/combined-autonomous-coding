import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

# Mock imports
sys.modules['agents.gemini.client'] = MagicMock()
sys.modules['shared.utils'] = MagicMock()

from shared.config import Config

class TestChatManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.config = Config(project_dir=self.project_dir)

        # Patching inside the test method or setup avoids import issues if modules are not yet created
        # But since we are creating shared/chat.py next, we can't import it yet in the global scope if we want to run this test immediately after creation without errors.
        # However, for this test file to be valid python, shared.chat must exist or be mocked.
        # Since I'm creating the test first, I will define the test but I can't import ChatManager until it exists.
        # So I will assume shared.chat will be created.
        pass

    async def test_initialization(self):
        from shared.chat import ChatManager
        manager = ChatManager(self.project_dir)
        self.assertEqual(manager.project_dir, self.project_dir)
        self.assertEqual(len(manager.history), 0)

    async def test_build_prompt(self):
        from shared.chat import ChatManager
        manager = ChatManager(self.project_dir)

        # Mock history
        manager.history = [
            {"role": "user", "content": "Hello"},
            {"role": "agent", "content": "Hi there"}
        ]

        with patch('shared.chat.get_file_tree', return_value="mock_tree"):
            prompt = manager._build_prompt("How are you?")

        self.assertIn("mock_tree", prompt)
        self.assertIn("Hello", prompt)
        self.assertIn("Hi there", prompt)
        self.assertIn("How are you?", prompt)

    @patch('shared.chat.GeminiClient')
    @patch('shared.chat.process_response_blocks', new_callable=AsyncMock)
    async def test_process_turn(self, mock_process_blocks, MockClient):
        from shared.chat import ChatManager

        # Setup mocks
        mock_client_instance = MockClient.return_value
        mock_client_instance.run_command = AsyncMock(return_value={"content": "I will run ls\n```bash\nls\n```"})

        mock_process_blocks.return_value = ("log output", ["Ran Bash: ls"])

        manager = ChatManager(self.project_dir)

        # Run process_turn
        response = await manager._process_turn("list files")

        # Verification
        self.assertEqual(response, "I will run ls\n```bash\nls\n```")
        self.assertEqual(len(manager.history), 2) # User + Agent

        # Check history content
        self.assertEqual(manager.history[0]['role'], 'user')
        self.assertEqual(manager.history[0]['content'], 'list files')
        self.assertEqual(manager.history[1]['role'], 'agent')
        self.assertIn("I will run ls", manager.history[1]['content'])
        self.assertIn("log output", manager.history[1]['content']) # Tool output should be appended

if __name__ == '__main__':
    unittest.main()
