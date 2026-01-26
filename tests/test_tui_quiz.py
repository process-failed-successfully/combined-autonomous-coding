import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Label, Button, RichLog, Markdown
from shared.tui_quiz import QuizTab
from shared.quiz import Question

class QuizTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield QuizTab(self.project_dir)

class TestQuizTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = QuizTestApp(self.project_dir)

    @patch("shared.quiz.QuizGenerator.generate_questions")
    @patch("shared.quiz.scan_project") # Mock scan to avoid FS access
    async def test_quiz_flow(self, mock_scan, mock_gen):
        mock_scan.return_value = {} # Empty map fine since we mock generation

        # Mock questions
        q1 = Question("Q1", ["A", "B"], 0, "Exp1")
        q2 = Question("Q2", ["C", "D"], 1, "Exp2")

        # return_value is for the first call, side_effect for subsequent?
        # Actually generate_questions is called inside start_new_game -> load_next_question
        # and then when Next is clicked.
        mock_gen.side_effect = [[q1], [q2]]

        async with self.app.run_test(size=(80, 24)) as pilot:
            tab = self.app.query_one(QuizTab)

            # Verify initialization
            self.assertEqual(tab.score, 0)
            self.assertIsNotNone(tab.current_question)
            self.assertEqual(tab.current_question.text, "Q1")

            # Click Correct Answer (Option 0 -> A)
            await pilot.click("#quiz-opt-0")

            # Verify Score
            self.assertEqual(tab.score, 1)

            # Click Next
            await pilot.click("#btn-quiz-next")

            # Verify Q2 loaded
            self.assertEqual(tab.current_question.text, "Q2")

            # Click Incorrect Answer (Option 0 -> C, Correct is 1 -> D)
            await pilot.click("#quiz-opt-0")

            # Verify Score unchanged
            self.assertEqual(tab.score, 1)

if __name__ == "__main__":
    unittest.main()
