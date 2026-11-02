import unittest
from unittest.mock import patch, MagicMock
from shared.levenshtein_lab import LevenshteinLabManager, run_levenshtein_lab_logic
from shared.tui_levenshtein import LevenshteinLabTab
from textual.app import App
import sys
import io


class TestLevenshteinLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = LevenshteinLabManager()

    def test_distance_same_strings(self):
        self.assertEqual(self.manager.distance("test", "test"), 0)

    def test_distance_empty_string(self):
        self.assertEqual(self.manager.distance("", "test"), 4)
        self.assertEqual(self.manager.distance("test", ""), 4)

    def test_distance_different_strings(self):
        self.assertEqual(self.manager.distance("kitten", "sitting"), 3)
        self.assertEqual(self.manager.distance("flaw", "lawn"), 2)

    def test_similarity(self):
        self.assertAlmostEqual(self.manager.similarity("test", "test"), 1.0)
        self.assertAlmostEqual(self.manager.similarity("", "test"), 0.0)
        # kitten (6), sitting (7), distance 3, max 7. (7-3)/7 = 4/7 = 0.5714...
        self.assertAlmostEqual(self.manager.similarity("kitten", "sitting"), 4/7)


class TestLevenshteinLabCLI(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_run_distance(self, mock_exit, mock_stdout):
        args = MagicMock()
        args.action = "distance"
        args.string1 = "kitten"
        args.string2 = "sitting"

        run_levenshtein_lab_logic(args)

        mock_exit.assert_called_once_with(0)
        output = mock_stdout.getvalue()
        self.assertIn('"distance": 3', output)
        self.assertIn('"similarity": 0.5714', output)


class DummyApp(App):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def compose(self):
        yield self.tab


class TestLevenshteinLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_levenshtein_tui_render(self):
        tab = LevenshteinLabTab(project_dir=MagicMock())
        app = DummyApp(tab)
        async with app.run_test() as pilot:
            # Inputs should be available
            str1_input = app.query_one("#levenshtein-str1")
            str2_input = app.query_one("#levenshtein-str2")

            str1_input.value = "kitten"
            str2_input.value = "sitting"

            # evaluate_distance should run on change
            tab.evaluate_distance()

            log = app.query_one("#levenshtein-results-log")

            # Wait for text to update
            await pilot.pause(0.1)

            log_text = "".join(line.text for line in log.lines)

            self.assertIn('"distance": 3', log_text)
            self.assertIn('"similarity": "57.14%"', log_text)
