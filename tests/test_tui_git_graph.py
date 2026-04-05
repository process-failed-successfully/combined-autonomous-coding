import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Button
from shared.tui_git_graph import GitGraphPane

class TestGitGraphPane(unittest.IsolatedAsyncioTestCase):
    async def test_load_graph(self):
        project_dir = Path("/tmp/test_project")
        pane = GitGraphPane(project_dir)

        # Create a test app
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield pane

        app = TestApp()

        # Patch the helper function
        with patch("shared.tui_git_graph.get_git_graph_lines") as mock_get_lines:
            mock_get_lines.return_value = ["* a1b2c3d (HEAD -> main) Initial commit", "|"]

            async with app.run_test() as pilot:
                # Trigger load (happens on mount, but let's wait)
                await pilot.pause(0.1)

                # Check RichLog content
                log_view = pane.query_one("#git-graph-view", RichLog)

                # Verify that lines were written

                # Wait for the async task to finish
                await pilot.pause(0.1)

                self.assertTrue(len(log_view.lines) >= 2)
                self.assertIn("* a1b2c3d", log_view.lines[0].text)

                # Test Refresh Button
                mock_get_lines.return_value = ["* new_commit", "|"]
                app.query_one("#btn-refresh-graph").press()
        await pilot.pause()
                await pilot.pause(0.1)

                self.assertIn("* new_commit", log_view.lines[0].text)

if __name__ == "__main__":
    unittest.main()
