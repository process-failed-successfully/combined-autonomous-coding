import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import yaml

from shared.guardrails import GuardrailsManager, NamingPolicy, StructurePolicy, ContentPolicy, MetricPolicy, Violation

class TestGuardrails(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_naming_policy(self):
        config = {
            "type": "naming",
            "files": "**/*.py",
            "rules": [
                {"pattern": "^[a-z_]+\\.py$", "message": "Snake case required"}
            ]
        }
        policy = NamingPolicy("Naming", config)

        # Create good file
        (self.test_dir / "good_file.py").touch()
        # Create bad file
        (self.test_dir / "BadFile.py").touch()

        violations = policy.check(self.test_dir)
        self.assertEqual(len(violations), 1)
        self.assertIn("BadFile.py", violations[0].message)

    def test_structure_policy(self):
        config = {
            "type": "structure",
            "path": "src",
            "required_files": ["__init__.py", "README.md"]
        }
        policy = StructurePolicy("Structure", config)

        src_dir = self.test_dir / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").touch()
        # README.md missing

        violations = policy.check(self.test_dir)
        self.assertEqual(len(violations), 1)
        self.assertIn("README.md", violations[0].message)

    def test_content_policy(self):
        config = {
            "type": "content",
            "files": "**/*.py",
            "banned_patterns": ["print\\("]
        }
        policy = ContentPolicy("Content", config)

        file_path = self.test_dir / "test.py"
        file_path.write_text("def foo():\n    print('hello')\n")

        violations = policy.check(self.test_dir)
        self.assertEqual(len(violations), 1)
        self.assertIn("Found banned pattern", violations[0].message)
        self.assertEqual(violations[0].line, 2)

    @patch("shared.guardrails.analyze_project_complexity")
    def test_metric_policy(self, mock_complexity):
        config = {
            "type": "metric",
            "metric": "complexity",
            "files": "**/*.py",
            "max": 5
        }
        policy = MetricPolicy("Metric", config)

        # Mock complexity return
        mock_complexity.return_value = [
            {"file": "complex.py", "function": "complex_func", "complexity": 10, "lineno": 1},
            {"file": "simple.py", "function": "simple_func", "complexity": 2, "lineno": 1}
        ]

        # Files must exist for _matches_file check if we implemented strict globbing,
        # but our policy implementation might try to resolve paths.
        # Actually, MetricPolicy calls analyze_project_complexity which returns relative paths.
        # Then it does `project_dir / res["file"]` and checks _matches_file.
        # So files should exist or at least match pattern.

        (self.test_dir / "complex.py").touch()
        (self.test_dir / "simple.py").touch()

        violations = policy.check(self.test_dir)
        self.assertEqual(len(violations), 1)
        self.assertIn("Complexity 10", violations[0].message)

    def test_manager_load_config(self):
        config_path = self.test_dir / "guardrails.yaml"
        config_data = [
            {"name": "Policy1", "type": "naming"}
        ]
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        manager = GuardrailsManager(self.test_dir)
        self.assertEqual(len(manager.policies), 1)
        self.assertIsInstance(manager.policies[0], NamingPolicy)

    def test_manager_create_default(self):
        manager = GuardrailsManager(self.test_dir)
        path = manager.create_default_config()
        self.assertTrue(path.exists())

        # Reload
        manager.load_config()
        self.assertGreater(len(manager.policies), 0)

if __name__ == "__main__":
    unittest.main()
