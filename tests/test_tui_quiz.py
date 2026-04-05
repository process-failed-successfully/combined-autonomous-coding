import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App
from textual.widgets import Markdown, Button
from shared.tui_quiz import QuizTab
from shared.quiz import QuizQuestion

class TestQuizTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_questions = [
            QuizQuestion("Q1", ["A", "B", "C", "D"], 0, "Exp1"),
            QuizQuestion("Q2", ["E", "F", "G", "H"], 1, "Exp2")
        ]

    @patch("shared.tui_quiz.QuizGenerator")
    async def test_quiz_flow(self, mock_gen_class):
        mock_gen_instance = mock_gen_class.return_value
        mock_gen_instance.generate_questions.return_value = self.mock_questions

        with patch.object(Path, 'resolve', return_value=Path("/mock/project")):
            tab = QuizTab(Path("."))

        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()

        # Increase height to ensure all buttons are visible
        async with app.run_test(size=(80, 40)) as pilot:
            await pilot.pause(2.0)

            # Click Correct Answer Q1
            app.query_one("#btn-opt-0").press()
        await pilot.pause()
            await pilot.pause(0.5)

            # Click Next Question
            app.query_one("#btn-quiz-next").press()
        await pilot.pause()
            await pilot.pause(0.5)

            # Click Incorrect Answer Q2 (Button 3)
            # This failed before due to screen size clipping
            app.query_one("#btn-opt-3").press()
        await pilot.pause()
            await pilot.pause(0.5)

            # Verify feedback
            feedback = tab.query_one("#quiz-feedback")
            self.assertIn("Incorrect.", str(feedback.render()))

            # Click Next Question (End Game)
            app.query_one("#btn-quiz-next").press()
        await pilot.pause()
            await pilot.pause(0.5)

            # Verify Game Over
            score_label = tab.query_one("#quiz-score")
            self.assertIn("Final Score: 1/2", str(score_label.render()))
