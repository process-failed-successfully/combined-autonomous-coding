import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
from shared.map import scan_project, CodeNode

@dataclass
class Question:
    text: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = None

class QuizGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.map_data = {}

    def load_data(self):
        """Scans the project to load code structure."""
        if not self.map_data:
            self.map_data = scan_project(self.project_dir)

    def generate_questions(self, count: int = 5) -> List[Question]:
        """Generates a list of random questions about the codebase."""
        self.load_data()
        if not self.map_data:
            return [Question("No Python code found in project.", ["OK"], 0)]

        questions = []
        generators = [
            self._gen_class_location,
            self._gen_function_location,
            self._gen_dependency
        ]

        for _ in range(count):
            gen = random.choice(generators)
            q = gen()
            if q:
                questions.append(q)

        return questions

    def _get_all_files(self) -> List[str]:
        return list(self.map_data.keys())

    def _gen_class_location(self) -> Optional[Question]:
        """Generates a question: Where is class X defined?"""
        # Find all classes
        classes = []
        for file_path, node in self.map_data.items():
            for child in node.children:
                if child.type == 'class':
                    classes.append((child.name, file_path))

        if not classes:
            return None

        target_class, correct_file = random.choice(classes)

        # Distractors: other files
        all_files = self._get_all_files()
        distractors = [f for f in all_files if f != correct_file]

        if len(distractors) < 3:
            return None # Not enough files for meaningful multiple choice

        # Pick 3 random distractors
        choices = random.sample(distractors, min(3, len(distractors)))
        choices.append(correct_file)
        random.shuffle(choices)

        return Question(
            text=f"In which file is the class '{target_class}' defined?",
            options=choices,
            correct_index=choices.index(correct_file),
            explanation=f"'{target_class}' is defined in '{correct_file}'."
        )

    def _gen_function_location(self) -> Optional[Question]:
        """Generates a question: Where is function X defined?"""
        functions = []
        for file_path, node in self.map_data.items():
            for child in node.children:
                if child.type == 'function':
                    functions.append((child.name, file_path))

        if not functions:
            return None

        target_func, correct_file = random.choice(functions)

        all_files = self._get_all_files()
        distractors = [f for f in all_files if f != correct_file]

        if len(distractors) < 3:
            return None

        choices = random.sample(distractors, min(3, len(distractors)))
        choices.append(correct_file)
        random.shuffle(choices)

        return Question(
            text=f"In which file is the function '{target_func}' defined?",
            options=choices,
            correct_index=choices.index(correct_file),
            explanation=f"'{target_func}' is defined in '{correct_file}'."
        )

    def _gen_dependency(self) -> Optional[Question]:
        """Generates a question: What does file X import?"""
        files_with_deps = []
        for file_path, node in self.map_data.items():
            if node.dependencies:
                files_with_deps.append((file_path, list(node.dependencies)))

        if not files_with_deps:
            return None

        target_file, deps = random.choice(files_with_deps)
        correct_dep = random.choice(deps)

        # Distractors: deps from other files or just random strings?
        # Better: deps from other files to look realistic
        all_deps = set()
        for _, node in self.map_data.items():
            all_deps.update(node.dependencies)

        distractors = [d for d in all_deps if d not in deps]

        if len(distractors) < 3:
            return None

        choices = random.sample(distractors, min(3, len(distractors)))
        choices.append(correct_dep)
        random.shuffle(choices)

        return Question(
            text=f"Which of the following is imported by '{target_file}'?",
            options=choices,
            correct_index=choices.index(correct_dep),
            explanation=f"'{target_file}' imports '{correct_dep}'."
        )
