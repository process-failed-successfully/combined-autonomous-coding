
import unittest
import shutil
import tempfile
from pathlib import Path
from shared.dockerizer import Dockerizer


class TestDockerizer(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.dockerizer = Dockerizer(self.project_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_detect_python_requirements(self):
        (self.project_dir / "requirements.txt").touch()
        self.assertEqual(self.dockerizer.detect_project_type(), "python")

    def test_detect_python_pyproject(self):
        (self.project_dir / "pyproject.toml").touch()
        self.assertEqual(self.dockerizer.detect_project_type(), "python")

    def test_detect_node(self):
        (self.project_dir / "package.json").touch()
        self.assertEqual(self.dockerizer.detect_project_type(), "node")

    def test_detect_go(self):
        (self.project_dir / "go.mod").touch()
        self.assertEqual(self.dockerizer.detect_project_type(), "go")

    def test_detect_unknown(self):
        self.assertEqual(self.dockerizer.detect_project_type(), "unknown")

    def test_generate_python_dockerfile_defaults(self):
        dockerfile = self.dockerizer.generate_dockerfile("python")
        self.assertIn("FROM python:3.10-slim", dockerfile)
        self.assertIn('CMD ["python", "app.py"]', dockerfile)  # Default fallback

    def test_generate_python_dockerfile_main(self):
        (self.project_dir / "main.py").touch()
        dockerfile = self.dockerizer.generate_dockerfile("python")
        self.assertIn('CMD ["python", "main.py"]', dockerfile)

    def test_generate_python_dockerfile_requirements(self):
        (self.project_dir / "requirements.txt").touch()
        dockerfile = self.dockerizer.generate_dockerfile("python")
        self.assertIn("COPY requirements.txt .", dockerfile)
        self.assertIn("RUN pip install", dockerfile)

    def test_generate_node_dockerfile(self):
        dockerfile = self.dockerizer.generate_dockerfile("node")
        self.assertIn("FROM node:18-alpine", dockerfile)
        self.assertIn("RUN npm install", dockerfile)
        self.assertIn('CMD ["npm", "start"]', dockerfile)

    def test_generate_go_dockerfile(self):
        dockerfile = self.dockerizer.generate_dockerfile("go")
        self.assertIn("FROM golang:1.21-alpine", dockerfile)
        self.assertIn("RUN go build -o main .", dockerfile)

    def test_generate_compose_node(self):
        compose = self.dockerizer.generate_docker_compose("node")
        self.assertIn('ports:', compose)
        self.assertIn('- "3000:3000"', compose)

    def test_generate_compose_python(self):
        compose = self.dockerizer.generate_docker_compose("python")
        self.assertIn('- "8000:8000"', compose)

    def test_generate_dockerignore_python(self):
        ignore = self.dockerizer.generate_dockerignore("python")
        self.assertIn("__pycache__", ignore)
        self.assertIn(".venv", ignore)

    def test_generate_dockerignore_node(self):
        ignore = self.dockerizer.generate_dockerignore("node")
        self.assertIn("node_modules", ignore)


if __name__ == '__main__':
    unittest.main()
