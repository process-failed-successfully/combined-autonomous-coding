import unittest
from pathlib import Path
import tempfile
from shared.cicd import CICDGenerator


class TestCICDGenerator(unittest.TestCase):

    def test_detect_python(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "requirements.txt").touch()

            generator = CICDGenerator(project_dir)
            self.assertEqual(generator.detect_project_type(), "python")

    def test_detect_node(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "package.json").touch()

            generator = CICDGenerator(project_dir)
            self.assertEqual(generator.detect_project_type(), "node")

    def test_detect_go(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "go.mod").touch()

            generator = CICDGenerator(project_dir)
            self.assertEqual(generator.detect_project_type(), "go")

    def test_detect_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            generator = CICDGenerator(project_dir)
            self.assertEqual(generator.detect_project_type(), "unknown")

    def test_generate_github_python(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "requirements.txt").touch()

            generator = CICDGenerator(project_dir)
            files = generator.generate("github")

            self.assertIn(".github/workflows/ci.yml", files)
            content = files[".github/workflows/ci.yml"]
            self.assertIn("name: Python CI", content)
            self.assertIn("pip install -r requirements.txt", content)

    def test_generate_gitlab_node(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "package.json").touch()

            generator = CICDGenerator(project_dir)
            files = generator.generate("gitlab")

            self.assertIn(".gitlab-ci.yml", files)
            content = files[".gitlab-ci.yml"]
            self.assertIn("image: node:latest", content)
            self.assertIn("npm install", content)

    def test_unsupported_platform(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_dir = Path(tmpdirname)
            (project_dir / "requirements.txt").touch()

            generator = CICDGenerator(project_dir)
            with self.assertRaises(ValueError):
                generator.generate("azure")


if __name__ == '__main__':
    unittest.main()
