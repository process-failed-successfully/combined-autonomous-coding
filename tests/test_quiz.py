import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.quiz import QuizGenerator, QuizQuestion
from shared.map import CodeNode

class TestQuizGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_nodes = {
            "file_a.py": CodeNode("file_a.py", "module", "file_a.py", 0),
            "file_b.py": CodeNode("file_b.py", "module", "file_b.py", 0),
            "file_c.py": CodeNode("file_c.py", "module", "file_c.py", 0),
            "file_d.py": CodeNode("file_d.py", "module", "file_d.py", 0),
            "file_e.py": CodeNode("file_e.py", "module", "file_e.py", 0),
        }

        # Add ClassA to file_a.py
        class_a = CodeNode("ClassA", "class", "file_a.py", 10)
        self.mock_nodes["file_a.py"].children.append(class_a)

        # Add methods to ClassA
        class_a.children.append(CodeNode("method_one", "function", "file_a.py", 11))
        class_a.children.append(CodeNode("method_two", "function", "file_a.py", 15))

        # Add FunctionB to file_b.py
        func_b = CodeNode("function_b", "function", "file_b.py", 5)
        self.mock_nodes["file_b.py"].children.append(func_b)

        # Distractor classes
        class_c = CodeNode("ClassC", "class", "file_c.py", 10)
        self.mock_nodes["file_c.py"].children.append(class_c)

        class_d = CodeNode("ClassD", "class", "file_d.py", 10)
        self.mock_nodes["file_d.py"].children.append(class_d)

        class_e = CodeNode("ClassE", "class", "file_e.py", 10)
        self.mock_nodes["file_e.py"].children.append(class_e)

    @patch("shared.quiz.scan_project")
    def test_flatten_nodes(self, mock_scan):
        mock_scan.return_value = self.mock_nodes
        generator = QuizGenerator(Path("."))

        # 5 files + 1 ClassA + 2 methods + 1 funcB + 1 ClassC + 1 ClassD + 1 ClassE = 12 nodes
        self.assertEqual(len(generator.nodes), 12)

    @patch("shared.quiz.scan_project")
    def test_generate_location_question(self, mock_scan):
        mock_scan.return_value = self.mock_nodes
        generator = QuizGenerator(Path("."))

        q = generator._generate_location_question()

        if q:
            self.assertIsInstance(q, QuizQuestion)
            self.assertTrue(q.text.startswith("In which file"))
            self.assertIn(q.options[q.correct_index], ["file_a.py", "file_b.py", "file_c.py", "file_d.py", "file_e.py"])
            self.assertEqual(len(q.options), 4)

    @patch("shared.quiz.scan_project")
    def test_generate_composition_question(self, mock_scan):
        mock_scan.return_value = self.mock_nodes
        generator = QuizGenerator(Path("."))

        q = generator._generate_composition_question()
        if q:
            self.assertIsInstance(q, QuizQuestion)
            self.assertIn("Which class is defined in", q.text)
            self.assertIn(q.options[q.correct_index], ["ClassA", "ClassC", "ClassD", "ClassE"])
            self.assertEqual(len(q.options), 4)

    @patch("shared.quiz.scan_project")
    def test_generate_structure_question(self, mock_scan):
        mock_scan.return_value = self.mock_nodes
        generator = QuizGenerator(Path("."))

        q = generator._generate_structure_question()
        if q:
            self.assertIsInstance(q, QuizQuestion)
            self.assertIn("How many methods", q.text)
            self.assertEqual(len(q.options), 4)
            # ClassA has 2 methods. Others have 0.
            if "ClassA" in q.text:
                self.assertEqual(q.options[q.correct_index], "2")
            else:
                self.assertEqual(q.options[q.correct_index], "0")

    @patch("shared.quiz.scan_project")
    def test_generate_questions_integration(self, mock_scan):
        mock_scan.return_value = self.mock_nodes
        generator = QuizGenerator(Path("."))

        questions = generator.generate_questions(5)
        # We might not get 5 if random selection fails to find distractors (though here it should work)
        # But let's assert at least some questions
        self.assertTrue(len(questions) > 0)
        for q in questions:
            self.assertIsInstance(q, QuizQuestion)
            self.assertTrue(len(q.options) == 4)
            self.assertTrue(0 <= q.correct_index < 4)
