import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_presentation import PresentationTab


class PresentationTestApp(App[None]):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield PresentationTab(self.project_dir)


class TestPresentationTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = PresentationTestApp(self.project_dir)

    @patch("shared.tui_presentation.PresentationGenerator")
    async def test_generate_presentation(self, mock_generator_cls):
        # Mock generator instance and generate method
        mock_generator = mock_generator_cls.return_value
        mock_generator.generate = AsyncMock(return_value=True)

        async with self.app.run_test() as pilot:
            # Click generate
            await pilot.click("#btn-pres-generate")

            # Wait for background task
            await pilot.pause(2.0)

            # Verify generate was called
            mock_generator.generate.assert_called_once()

            args, _ = mock_generator.generate.call_args
            # args[0] is output_path, args[1] is theme
            self.assertEqual(args[0].name, "presentation.md")
            self.assertEqual(args[1], "default")

    @patch("shared.tui_presentation.PresentationGenerator")
    async def test_generate_presentation_failure(self, mock_generator_cls):
        # Mock generator instance to raise exception
        mock_generator = mock_generator_cls.return_value
        mock_generator.generate = AsyncMock(side_effect=Exception("Simulated failure"))

        async with self.app.run_test() as pilot:
            # Patch notify on the app to verify error handling
            # Note: We must patch it on the app instance running in the pilot
            self.app.notify = MagicMock()

            # Click generate
            await pilot.click("#btn-pres-generate")

            # Wait for background task
            await pilot.pause(2.0)

            # Verify generate was called
            mock_generator.generate.assert_called_once()

            # Verify notification was sent with error
            # We look for a call that contains the error message
            found = False
            for call in self.app.notify.call_args_list:
                args, kwargs = call
                if args and "Simulated failure" in args[0] and kwargs.get("severity") == "error":
                    found = True
                    break

            self.assertTrue(found, "Error notification not found in calls")


if __name__ == "__main__":
    unittest.main()
