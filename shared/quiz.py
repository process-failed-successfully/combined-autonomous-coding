from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import random
from shared.map import scan_project, CodeNode

@dataclass
class QuizQuestion:
    text: str
    options: List[str]
    correct_index: int
    explanation: str

class QuizGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.map_data = scan_project(self.project_dir)
        self.nodes = self._flatten_nodes(self.map_data)

    def _flatten_nodes(self, map_data: Dict[str, CodeNode]) -> List[CodeNode]:
        """Flattens the map data into a list of all nodes."""
        nodes = []
        for file_node in map_data.values():
            nodes.append(file_node)
            nodes.extend(self._get_all_children(file_node))
        return nodes

    def _get_all_children(self, node: CodeNode) -> List[CodeNode]:
        children = []
        for child in node.children:
            children.append(child)
            children.extend(self._get_all_children(child))
        return children

    def generate_questions(self, count: int = 10) -> List[QuizQuestion]:
        questions = []
        if not self.nodes:
            return []

        attempts = 0
        while len(questions) < count and attempts < count * 5:
            attempts += 1
            q_type = random.choice(["location", "composition", "structure"])
            question = None

            if q_type == "location":
                question = self._generate_location_question()
            elif q_type == "composition":
                question = self._generate_composition_question()
            elif q_type == "structure":
                question = self._generate_structure_question()

            if question:
                questions.append(question)

        return questions

    def _generate_location_question(self) -> Optional[QuizQuestion]:
        # Find a class or function
        candidates = [n for n in self.nodes if n.type in ("class", "function")]
        if not candidates:
            return None

        target = random.choice(candidates)
        correct_file = target.file

        # Distractors: other files
        all_files = list(set(n.file for n in self.nodes if n.file != correct_file))
        if len(all_files) < 3:
            return None # Not enough distractors

        distractors = random.sample(all_files, 3)
        options = distractors + [correct_file]
        random.shuffle(options)

        return QuizQuestion(
            text=f"In which file is the {target.type} '{target.name}' defined?",
            options=options,
            correct_index=options.index(correct_file),
            explanation=f"'{target.name}' is defined in {correct_file} at line {target.lineno}."
        )

    def _generate_composition_question(self) -> Optional[QuizQuestion]:
        # Find a file with at least one class
        files_with_classes = [n for n in self.nodes if n.type == "module" and any(c.type == "class" for c in n.children)]
        if not files_with_classes:
            return None

        target_file = random.choice(files_with_classes)
        target_class = next(c for c in target_file.children if c.type == "class")

        # Distractors: classes from other files
        other_classes = [n.name for n in self.nodes if n.type == "class" and n.file != target_file.file]
        if len(other_classes) < 3:
            return None

        distractors = random.sample(other_classes, 3)
        options = distractors + [target_class.name]
        random.shuffle(options)

        return QuizQuestion(
            text=f"Which class is defined in '{target_file.name}'?",
            options=options,
            correct_index=options.index(target_class.name),
            explanation=f"'{target_class.name}' is a class defined in {target_file.name}."
        )

    def _generate_structure_question(self) -> Optional[QuizQuestion]:
        # Find a class
        classes = [n for n in self.nodes if n.type == "class"]
        if not classes:
            return None

        target = random.choice(classes)
        method_count = sum(1 for c in target.children if c.type == "function")

        # Distractors: random numbers close to count
        # Ensure unique and non-negative
        distractors = set()
        while len(distractors) < 3:
            d = method_count + random.randint(-3, 3)
            if d != method_count and d >= 0:
                distractors.add(d)

        options = [str(d) for d in distractors] + [str(method_count)]
        random.shuffle(options)

        return QuizQuestion(
            text=f"How many methods does the class '{target.name}' have?",
            options=options,
            correct_index=options.index(str(method_count)),
            explanation=f"'{target.name}' has {method_count} methods: {', '.join(c.name for c in target.children if c.type == 'function') or 'None'}."
        )
