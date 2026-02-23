"""
Typing Lab
==========

Logic for the Typing Tutor.
"""

import random
from pathlib import Path
from typing import Dict, Any, Optional
from shared.snippets import SnippetManager

DEFAULT_SNIPPETS = {
    "Hello World": """def hello_world():
    print("Hello, World!")""",

    "Fibonacci": """def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)""",

    "Class Example": """class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        return "Woof!" """,

    "List Comprehension": """numbers = [1, 2, 3, 4, 5]
squares = [n**2 for n in numbers]
print(squares)""",

    "Async IO": """import asyncio

async def main():
    print('Hello')
    await asyncio.sleep(1)
    print('World')"""
}

class TypingLabManager:
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self.snippet_manager = SnippetManager(project_dir) if project_dir else None

    def get_snippet(self, name: Optional[str] = None) -> str:
        """Returns snippet content."""
        if name:
            # Check defaults first
            if name in DEFAULT_SNIPPETS:
                return DEFAULT_SNIPPETS[name]
            # Then check manager
            if self.snippet_manager:
                content = self.snippet_manager.get_snippet(name)
                if content:
                    return content
            return f"# Snippet '{name}' not found."

        # Random default
        return random.choice(list(DEFAULT_SNIPPETS.values()))

    def list_options(self) -> Dict[str, str]:
        """Returns available snippets (name -> source)."""
        options = {k: "Built-in" for k in DEFAULT_SNIPPETS.keys()}
        if self.snippet_manager:
            for s in self.snippet_manager.list_snippets():
                options[s] = "User"
        return options

    def calculate_stats(self, original: str, typed: str, duration: float) -> Dict[str, float]:
        """
        Calculates WPM and Accuracy.
        WPM = (Characters / 5) / (Minutes)
        Accuracy = (Correct Characters / Total Typed Characters) * 100
        """
        if duration <= 0:
            return {"wpm": 0.0, "accuracy": 0.0, "progress": 0.0}

        # WPM
        # Standard definition: 5 chars = 1 word
        num_chars = len(typed)
        minutes = duration / 60
        wpm = (num_chars / 5) / minutes if minutes > 0 else 0

        # Accuracy
        correct_chars = 0
        min_len = min(len(original), len(typed))
        for i in range(min_len):
            if original[i] == typed[i]:
                correct_chars += 1

        accuracy = (correct_chars / num_chars * 100) if num_chars > 0 else 100.0

        # Progress
        progress = (len(typed) / len(original) * 100) if len(original) > 0 else 100.0

        return {
            "wpm": round(wpm, 1),
            "accuracy": round(accuracy, 1),
            "progress": round(progress, 1)
        }
