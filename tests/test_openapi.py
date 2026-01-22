import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.openapi import OpenAPIGenerator

class TestOpenAPIGenerator(unittest.TestCase): # type: ignore
    def setUp(self) -> None:
        self.project_dir = Path("/tmp/test_project")
        self.generator = OpenAPIGenerator(self.project_dir)

    @patch("shared.openapi.DependencyAnalyzer")
    def test_detect_framework_flask(self, MockAnalyzer: MagicMock) -> None:
        mock_instance = MockAnalyzer.return_value
        mock_instance.scan.return_value = {
            "python": [{"dependencies": [{"name": "Flask", "version": "2.0"}]}],
            "node": []
        }
        # Re-init to use mock
        self.generator = OpenAPIGenerator(self.project_dir)
        self.generator.analyzer = mock_instance # Force inject

        self.assertEqual(self.generator.detect_framework(), "flask")

    @patch("shared.openapi.DependencyAnalyzer")
    def test_detect_framework_fastapi(self, MockAnalyzer: MagicMock) -> None:
        mock_instance = MockAnalyzer.return_value
        mock_instance.scan.return_value = {
            "python": [{"dependencies": [{"name": "fastapi", "version": "0.68"}]}],
            "node": []
        }
        self.generator = OpenAPIGenerator(self.project_dir)
        self.generator.analyzer = mock_instance

        self.assertEqual(self.generator.detect_framework(), "fastapi")

    @patch("shared.openapi.DependencyAnalyzer")
    def test_detect_framework_express(self, MockAnalyzer: MagicMock) -> None:
        mock_instance = MockAnalyzer.return_value
        mock_instance.scan.return_value = {
            "python": [],
            "node": [{"dependencies": [{"name": "express", "version": "4.17"}]}]
        }
        self.generator = OpenAPIGenerator(self.project_dir)
        self.generator.analyzer = mock_instance

        self.assertEqual(self.generator.detect_framework(), "express")

    @patch("pathlib.Path.rglob")
    def test_scan_routes_flask(self, mock_rglob: MagicMock) -> None:
        # Mock file system
        app_py = MagicMock(spec=Path)
        app_py.is_file.return_value = True
        app_py.relative_to.return_value = Path("app.py")
        app_py.parts = ("app.py",)
        app_py.read_text.return_value = "@app.route('/')"

        other_py = MagicMock(spec=Path)
        other_py.is_file.return_value = True
        other_py.relative_to.return_value = Path("utils.py")
        other_py.parts = ("utils.py",)
        other_py.read_text.return_value = "def helper(): pass"

        mock_rglob.return_value = [app_py, other_py]

        routes = self.generator.scan_routes("flask")
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0], app_py)

    @patch("pathlib.Path.rglob")
    def test_scan_routes_fastapi(self, mock_rglob: MagicMock) -> None:
        # Mock file system
        main_py = MagicMock(spec=Path)
        main_py.is_file.return_value = True
        main_py.relative_to.return_value = Path("main.py")
        main_py.parts = ("main.py",)
        main_py.read_text.return_value = "app = FastAPI()"

        api_py = MagicMock(spec=Path)
        api_py.is_file.return_value = True
        api_py.relative_to.return_value = Path("routers/users.py")
        api_py.parts = ("routers", "users.py")
        api_py.read_text.return_value = "router = APIRouter()"

        mock_rglob.return_value = [main_py, api_py]

        routes = self.generator.scan_routes("fastapi")
        self.assertEqual(len(routes), 2)

if __name__ == "__main__":
    unittest.main()
