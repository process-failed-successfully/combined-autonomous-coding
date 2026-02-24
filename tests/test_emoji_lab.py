import unittest
from unittest.mock import MagicMock, patch
from shared.emoji_lab import EmojiLabManager, run_emoji_lab_logic

class TestEmojiLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = EmojiLabManager()
        # Mock the emoji dictionary for predictable testing
        self.manager.emojis = {
            "smile": "😄",
            "heart": "❤️",
            "rocket": "🚀",
            "thumbs_up": "👍"
        }

    def test_search(self):
        results = self.manager.search("smile")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], ("smile", "😄"))

        results = self.manager.search("SMile") # Case insensitive
        self.assertEqual(len(results), 1)

        results = self.manager.search("notfound")
        self.assertEqual(len(results), 0)

    def test_list_all(self):
        results = self.manager.list_all(limit=2)
        self.assertEqual(len(results), 2)

        results = self.manager.list_all(limit=10)
        self.assertEqual(len(results), 4)

    def test_random(self):
        name, char = self.manager.random()
        self.assertIn(name, self.manager.emojis)
        self.assertEqual(char, self.manager.emojis[name])

class TestRunEmojiLabLogic(unittest.TestCase):
    @patch('shared.emoji_lab.console')
    def test_search_action(self, mock_console):
        args = MagicMock()
        args.action = "search"
        args.query = "rocket"

        # We need to patch EmojiLabManager to use our mock data
        with patch('shared.emoji_lab.EmojiLabManager') as MockManager:
            manager_instance = MockManager.return_value
            manager_instance.search.return_value = [("rocket", "🚀")]

            run_emoji_lab_logic(args)

            manager_instance.search.assert_called_with("rocket")
            mock_console.print.assert_called() # Should print the table

    @patch('shared.emoji_lab.console')
    def test_random_action(self, mock_console):
        args = MagicMock()
        args.action = "random"

        with patch('shared.emoji_lab.EmojiLabManager') as MockManager:
            manager_instance = MockManager.return_value
            manager_instance.random.return_value = ("rocket", "🚀")

            run_emoji_lab_logic(args)

            manager_instance.random.assert_called()
            mock_console.print.assert_called()

if __name__ == '__main__':
    unittest.main()
