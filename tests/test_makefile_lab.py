import unittest
import os
import tempfile
from pathlib import Path
from shared.makefile_lab import MakefileLabManager

class TestMakefileLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MakefileLabManager()

    def test_generate_python(self):
        content = self.manager.generate("python")
        self.assertIn("Makefile for Python Project", content)
        self.assertIn("all: clean install lint test build", content)
        self.assertIn("pytest", content)
        self.assertIn("flake8", content)
        self.assertIn("find . -type d -name __pycache__", content)

    def test_generate_node(self):
        content = self.manager.generate("Node")
        self.assertIn("Makefile for Node Project", content)
        self.assertIn("npm run build", content)
        self.assertIn("npm test", content)

    def test_generate_go(self):
        content = self.manager.generate("GO")
        self.assertIn("Makefile for Go Project", content)
        self.assertIn("go build", content)
        self.assertIn("golangci-lint", content)

    def test_generate_rust(self):
        content = self.manager.generate("rust")
        self.assertIn("Makefile for Rust Project", content)
        self.assertIn("cargo build", content)
        self.assertIn("cargo test", content)
        self.assertIn("@echo 'Nothing to do for this target'", content) # Install is empty for rust

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            self.manager.generate("invalid_lang")

if __name__ == "__main__":
    unittest.main()
