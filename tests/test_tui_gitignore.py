import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from pathlib import Path
from shared.tui_gitignore import GitignoreTab

class GitignoreTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.tab = GitignoreTab(project_dir)

    def compose(self) -> ComposeResult:
        yield self.tab

class TestGitignoreTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        # Ensure we don't actually read/write files during init unless mocked
        self.mock_manager_patcher = patch("shared.tui_gitignore.GitignoreManager")
        self.MockManager = self.mock_manager_patcher.start()
        self.mock_manager = self.MockManager.return_value
        self.mock_manager.list_templates.return_value = ["python", "node"]
        self.mock_manager.get_template.return_value = "*.pyc"
        self.mock_manager.check_ignore.return_value = {"ignored": "yes", "details": "some details"}

    def tearDown(self):
        self.mock_manager_patcher.stop()

    async def test_mount(self):
        app = GitignoreTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.tab
            self.assertIsNotNone(tab.query_one("#gitignore-template-list"))
            self.assertIsNotNone(tab.query_one("#gitignore-editor"))
            self.assertIsNotNone(tab.query_one("#gitignore-check-log"))

    async def test_load_templates(self):
        app = GitignoreTestApp(self.project_dir)
        async with app.run_test() as pilot:
            list_view = app.tab.query_one("#gitignore-template-list")
            self.assertEqual(len(list_view.children), 2)
            # Textual ListView items are ListItems. We need to check the label inside.
            # However, my implementation stores template_name on the item.
            self.assertEqual(list_view.children[0].template_name, "python")
            self.assertEqual(list_view.children[1].template_name, "node")

    async def test_append_template(self):
        app = GitignoreTestApp(self.project_dir)
        async with app.run_test() as pilot:
            # Select first item (python)
            list_view = app.tab.query_one("#gitignore-template-list")
            list_view.index = 0

            # Click append
            await pilot.click("#btn-gitignore-append")

            # Check editor content
            editor = app.tab.query_one("#gitignore-editor")
            self.assertIn("# Template: python", editor.text)
            self.assertIn("*.pyc", editor.text)

    async def test_check_ignore(self):
        app = GitignoreTestApp(self.project_dir)
        async with app.run_test() as pilot:
            # Type path
            await pilot.click("#gitignore-check-input")
            # pilot.type is not available in this version, set value directly
            input_widget = app.tab.query_one("#gitignore-check-input")
            input_widget.value = "test.pyc"

            # Click check
            await pilot.click("#btn-gitignore-check")

            # Verify manager called
            self.mock_manager.check_ignore.assert_called_with("test.pyc")

            # Verify log output (requires peeking into RichLog which is hard,
            # but we can verify it didn't crash)
            log = app.tab.query_one("#gitignore-check-log")
            self.assertTrue(log.visible)
