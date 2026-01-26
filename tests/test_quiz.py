import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.quiz import QuizGenerator, Question
from shared.map import CodeNode

class TestQuizGenerator(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/mock_project")
        self.generator = QuizGenerator(self.project_dir)

    @patch("shared.quiz.scan_project")
    def test_generate_questions_class_location(self, mock_scan):
        # Mock map data
        file_a = CodeNode("file_a.py", "module", "file_a.py", 0)
        file_a.children.append(CodeNode("ClassA", "class", "file_a.py", 10))

        file_b = CodeNode("file_b.py", "module", "file_b.py", 0)
        file_b.children.append(CodeNode("ClassB", "class", "file_b.py", 20))

        file_c = CodeNode("file_c.py", "module", "file_c.py", 0)

        file_d = CodeNode("file_d.py", "module", "file_d.py", 0)

        mock_scan.return_value = {
            "file_a.py": file_a,
            "file_b.py": file_b,
            "file_c.py": file_c,
            "file_d.py": file_d
        }

        questions = self.generator.generate_questions(count=5)

        # We should have some questions
        self.assertTrue(len(questions) > 0)

        # Check if we have a class location question
        class_questions = [q for q in questions if "In which file is the class" in q.text]
        if class_questions:
            q = class_questions[0]
            self.assertTrue(len(q.options) == 4)
            correct_option = q.options[q.correct_index]
            self.assertTrue(correct_option in ["file_a.py", "file_b.py"])

    @patch("shared.quiz.scan_project")
    def test_generate_questions_dependency(self, mock_scan):
        # Mock map data with dependencies
        file_a = CodeNode("file_a.py", "module", "file_a.py", 0)
        file_a.dependencies.add("os")
        file_a.dependencies.add("sys")

        # Need other files/deps for distractors
        file_b = CodeNode("file_b.py", "module", "file_b.py", 0)
        file_b.dependencies.add("json")

        file_c = CodeNode("file_c.py", "module", "file_c.py", 0)
        file_c.dependencies.add("re")

        file_d = CodeNode("file_d.py", "module", "file_d.py", 0)
        file_d.dependencies.add("math")

        mock_scan.return_value = {
            "file_a.py": file_a,
            "file_b.py": file_b,
            "file_c.py": file_c,
            "file_d.py": file_d
        }

        # Force dependency generator
        self.generator.load_data()
        q = self.generator._gen_dependency()

        if q:
            self.assertTrue("Which of the following is imported by" in q.text)
            correct_ans = q.options[q.correct_index]
            # Since we pick randomly, we just ensure it's valid
            self.assertTrue(len(q.options) == 4)

if __name__ == "__main__":
    unittest.main()
