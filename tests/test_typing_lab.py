import unittest
import time
from shared.typing_lab import TypingLabManager

class TestTypingLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TypingLabManager()

    def test_get_snippet_default(self):
        snippet = self.manager.get_snippet("Hello World")
        self.assertIn("Hello, World!", snippet)

    def test_get_snippet_random(self):
        snippet = self.manager.get_snippet()
        self.assertIsInstance(snippet, str)
        self.assertTrue(len(snippet) > 0)

    def test_calculate_stats_perfect(self):
        text = "Hello World"
        stats = self.manager.calculate_stats(text, text, duration=60)
        # 11 chars. 11/5 = 2.2 words. 1 minute. WPM = 2.2
        self.assertAlmostEqual(stats["wpm"], 2.2)
        self.assertEqual(stats["accuracy"], 100.0)
        self.assertEqual(stats["progress"], 100.0)

    def test_calculate_stats_imperfect(self):
        target = "Hello World"
        typed = "Hello Werld" # 1 error
        # 11 chars typed.
        stats = self.manager.calculate_stats(target, typed, duration=60)
        self.assertAlmostEqual(stats["wpm"], 2.2)
        # Accuracy: 10/11 correct = 90.9%
        self.assertAlmostEqual(stats["accuracy"], 90.9, places=1)

    def test_calculate_stats_incomplete(self):
        target = "Hello World"
        typed = "Hello"
        stats = self.manager.calculate_stats(target, typed, duration=30)
        # 5 chars. 1 word. 0.5 min. WPM = 2.0
        self.assertAlmostEqual(stats["wpm"], 2.0)
        self.assertEqual(stats["accuracy"], 100.0)
        self.assertAlmostEqual(stats["progress"], 45.5, places=1)

if __name__ == '__main__':
    unittest.main()
