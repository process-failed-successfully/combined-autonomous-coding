import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Tree
from shared.tui_terraform import TerraformTab

# A simple app to host the tab for testing
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TerraformTab(project_dir=Path("."))

class TestTerraformTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestApp()

    async def test_initialization(self):
        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(TerraformTab)
            self.assertIsInstance(tab, TerraformTab)
            # Check buttons exist
            self.assertIsNotNone(tab.query_one("#btn-tf-init"))
            self.assertIsNotNone(tab.query_one("#btn-tf-plan"))

    @patch("shared.tui_terraform.TerraformManager")
    async def test_button_actions(self, MockManager):
        # Setup mock
        mock_instance = MockManager.return_value
        # Mock methods to return success
        mock_instance.init = MagicMock(return_value=True)
        mock_instance.plan = MagicMock(return_value=True)

        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(TerraformTab)
            # Inject the mock manager into the running tab instance
            tab.manager = mock_instance

            # Click Init
            app.query_one("#btn-tf-init").press()
        await pilot.pause()
            await pilot.pause()
            mock_instance.init.assert_called()

            # Click Plan
            app.query_one("#btn-tf-plan").press()
        await pilot.pause()
            await pilot.pause()
            mock_instance.plan.assert_called()

    @patch("shared.tui_terraform.TerraformManager")
    async def test_destroy_confirmation(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.destroy = MagicMock(return_value=True)

        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(TerraformTab)
            tab.manager = mock_instance

            # Click Destroy
            app.query_one("#btn-tf-destroy").press()
        await pilot.pause()
            await pilot.pause()

            # Confirm
            app.query_one("#confirm").press()
        await pilot.pause()
            await pilot.pause()

            mock_instance.destroy.assert_called_with(auto_approve=True)

    @patch("shared.tui_terraform.TerraformManager")
    async def test_state_explorer(self, MockManager):
        mock_instance = MockManager.return_value

        # Mock show output
        mock_json = """
        {
            "values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "test_resource.foo",
                            "type": "test_resource",
                            "name": "foo",
                            "values": {
                                "id": "123",
                                "name": "bar"
                            }
                        }
                    ]
                }
            }
        }
        """
        mock_instance.show = MagicMock(return_value=mock_json)

        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(TerraformTab)
            tab.manager = mock_instance

            # Refresh state
            app.query_one("#btn-tf-refresh").press()
        await pilot.pause()
            await pilot.pause()

            mock_instance.show.assert_called_with(json_format=True)

            # Verify tree population
            tree = tab.query_one("#tf-state-tree", Tree)

            # Let's wait a bit more to ensure task completes
            await pilot.pause(0.1)

            self.assertGreater(len(tree.root.children), 0)
            node_label = str(tree.root.children[0].label)

            self.assertIn("test_resource", node_label)
            self.assertIn("foo", node_label)
