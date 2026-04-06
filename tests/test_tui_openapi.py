import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Select, RichLog

# Add root to path so we can import shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_openapi import OpenAPILabTab

class DummyOpenAPIApp(App):
    """Dummy app for testing the OpenAPI tab."""
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield OpenAPILabTab(project_dir=self.project_dir)

class TestOpenAPILabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = DummyOpenAPIApp(self.project_dir)

    async def test_tab_instantiation(self):
        """Test that the OpenAPI tab initializes with all required widgets."""
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(OpenAPILabTab)
            self.assertIsNotNone(tab)

            # Check for specific widgets by ID
            output_input = self.app.query_one("#openapi-output-input", Input)
            self.assertIsNotNone(output_input)
            self.assertEqual(output_input.value, "openapi.yaml")

            agent_select = self.app.query_one("#openapi-agent-select", Select)
            self.assertIsNotNone(agent_select)
            self.assertEqual(agent_select.value, "gemini")

            model_input = self.app.query_one("#openapi-model-input", Input)
            self.assertIsNotNone(model_input)

            generate_btn = self.app.query_one("#btn-generate-openapi", Button)
            self.assertIsNotNone(generate_btn)

            rich_log = self.app.query_one("#openapi-log", RichLog)
            self.assertIsNotNone(rich_log)

    @patch("shared.tui_openapi.OpenAPIGenerator.generate", new_callable=MagicMock)
    @patch("shared.tui_openapi.OpenAPIGenerator.detect_framework")
    @patch("shared.tui_openapi.OpenAPIGenerator.scan_routes")
    async def test_generate_spec_success(self, mock_scan, mock_detect, mock_generate):
        """Test the generate_spec method triggers OpenAPIGenerator.generate successfully."""
        # Setup mocks
        mock_detect.return_value = "flask"
        mock_scan.return_value = [Path("/tmp/test_project/app.py")]

        # Make the async mock return True to indicate success
        async def mock_gen_impl(*args, **kwargs):
            return True
        mock_generate.side_effect = mock_gen_impl

        async with self.app.run_test() as pilot:
            # Trigger generation
            await pilot.click("#btn-generate-openapi")

            # Wait for background worker to complete
            await pilot.pause(0.5)

            # Assertions
            mock_detect.assert_called_once()
            mock_scan.assert_called_once_with("flask")

            # Verify generate was called with the right parameters
            mock_generate.assert_called_once()
            args, kwargs = mock_generate.call_args
            self.assertEqual(args[0], Path("openapi.yaml"))
            self.assertEqual(kwargs["agent_type"], "gemini")

    @patch("shared.tui_openapi.OpenAPIGenerator.scan_routes")
    @patch("shared.tui_openapi.OpenAPIGenerator.detect_framework")
    async def test_generate_spec_no_routes(self, mock_detect, mock_scan):
        """Test generation stops early if no routes are found."""
        mock_detect.return_value = "flask"
        mock_scan.return_value = []

        async with self.app.run_test() as pilot:
            await pilot.click("#btn-generate-openapi")
            await pilot.pause(0.1)

            log = self.app.query_one("#openapi-log", RichLog)
            log_text = "\n".join([line.text for line in log.lines])
            self.assertIn("No route files found", log_text)

if __name__ == "__main__":
    unittest.main()
