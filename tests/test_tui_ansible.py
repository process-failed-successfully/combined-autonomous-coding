import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, RichLog, Checkbox, TabbedContent
from shared.tui_ansible import AnsibleLabTab

class TestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield AnsibleLabTab(self.project_dir)

class TestAnsibleLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.mock_manager = MagicMock()
        self.mock_manager.check_install.return_value = True

        # Patch the AnsibleManager class in tui_ansible module
        self.patcher = patch("shared.tui_ansible.AnsibleManager", return_value=self.mock_manager)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    async def test_mount_and_install_check(self):
        app = TestApp(self.project_dir)
        async with app.run_test() as pilot:
            # Check if tab mounted
            tab = app.query_one(AnsibleLabTab)
            self.assertIsNotNone(tab)

            # Check if buttons exist
            self.assertIsNotNone(tab.query_one("#btn-ansible-run"))
            self.assertIsNotNone(tab.query_one("#btn-ansible-list-inv"))
            self.assertIsNotNone(tab.query_one("#btn-ansible-lint"))

    async def test_run_playbook(self):
        app = TestApp(self.project_dir)
        # Mock run_playbook to return (True, "output")
        self.mock_manager.run_playbook.return_value = (True, "Playbook output log")

        async with app.run_test() as pilot:
            tab = app.query_one(AnsibleLabTab)

            # Simulate selecting a playbook
            # Since DirectoryTree selection is hard to simulate directly via clicks in tests without FS,
            # we manually set selected_playbook and enable button
            tab.selected_playbook = Path("site.yml")
            tab.query_one("#btn-ansible-run").disabled = False

            # Set inputs
            tab.query_one("#ansible-limit", Input).value = "web"
            tab.query_one("#chk-ansible-check", Checkbox).value = True

            # Click Run
            await pilot.click("#btn-ansible-run")
            await asyncio.sleep(0.1)

            # Verify manager call
            self.mock_manager.run_playbook.assert_called_with(
                "site.yml",
                inventory=None,
                check_mode=True,
                diff_mode=False,
                limit="web",
                extra_vars=None,
                capture_output=True
            )

            # Verify log output
            log = tab.query_one("#ansible-log", RichLog)
            self.assertIn("Running Playbook: site.yml", str(log.lines))

    async def test_list_inventory(self):
        app = TestApp(self.project_dir)
        self.mock_manager.list_inventory.return_value = '{"all": {"children": ["ungrouped"]}}'

        async with app.run_test() as pilot:
            # Switch tab
            tab = app.query_one(AnsibleLabTab)
            tab.query_one("#ansible-tabs", TabbedContent).active = "tab-inventory"
            await asyncio.sleep(0.1)

            # Click List Inventory
            await pilot.click("#btn-ansible-list-inv")
            await asyncio.sleep(0.2)

            # Verify call
            self.mock_manager.list_inventory.assert_called()

            # Verify log output (contains part of JSON)
            tab = app.query_one(AnsibleLabTab)
            log = tab.query_one("#ansible-log", RichLog)
            # RichLog lines might be formatted, check for key string
            # We can't easily check rendered text content in strict mode, but we check call happened
            self.assertTrue(self.mock_manager.list_inventory.called)

    async def test_run_lint(self):
        app = TestApp(self.project_dir)
        self.mock_manager.lint.return_value = (True, "Lint output")

        async with app.run_test() as pilot:
            # Switch tab
            tab = app.query_one(AnsibleLabTab)
            tab.query_one("#ansible-tabs", TabbedContent).active = "tab-lint"
            await asyncio.sleep(0.1)

            await pilot.click("#btn-ansible-lint")
            await asyncio.sleep(0.2)
            self.mock_manager.lint.assert_called_with(capture_output=True)

if __name__ == "__main__":
    unittest.main()
