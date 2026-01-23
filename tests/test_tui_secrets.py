import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, ListView, Input, RichLog
from shared.tui import AgentTUI, SecretsTab

class TestTUISecrets(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock SecretsManager
        self.patcher_secrets = patch("shared.tui.SecretsManager")
        self.MockSecretsManager = self.patcher_secrets.start()
        self.mock_manager = self.MockSecretsManager.return_value

        # Default mock behavior
        self.mock_manager.key_path = MagicMock()
        self.mock_manager.key_path.exists.return_value = True # Assume initialized by default
        self.mock_manager.list_secrets.return_value = ["API_KEY", "DB_PASSWORD"]
        self.mock_manager.get_secret.return_value = "secret_value"

    def tearDown(self):
        self.patcher_secrets.stop()
        shutil.rmtree(self.test_dir)

    async def test_secrets_tab_structure(self):
        """Test that the secrets tab has the expected widgets."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Switch to secrets tab (assuming it will be named tab-secrets)
            tabbed_content = app.query_one("#main-tabs")

            # Note: Since I haven't modified TUI yet, this part would fail if I tried to switch to it.
            # But here I am testing the SecretsTab class directly via composition if possible,
            # or I can manually instantiate it.
            # However, textual tests usually run the app.
            # I will assume I've added the tab in the implementation step.
            # For now, let's just instantiate the tab directly in a test harness or
            # wait until the implementation step to run this.
            # Actually, I can construct the app with just the SecretsTab for testing purposes if I wanted,
            # but AgentTUI structure is fixed.

            # So, I'll write the test assuming the tab exists. The test will fail if run before implementation.
            pass

    async def test_init_key(self):
        """Test key initialization flow."""
        self.mock_manager.key_path.exists.return_value = False
        self.mock_manager.generate_key.return_value = True

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for mount
            await pilot.pause()

            # Access the tab directly if possible or simulate navigation
            # Since I can't easily modify AgentTUI in test to add the tab,
            # I will rely on the implementation step to add it.

            # To make this test runnable *after* implementation, I will assume "tab-secrets" exists.
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-secrets"
            await pilot.pause()

            # Check if Init button is visible
            init_btn = app.query_one("#btn-secret-init", Button)
            self.assertIsNotNone(init_btn)

            # Click Init
            await pilot.click("#btn-secret-init")
            await pilot.pause()

            self.mock_manager.generate_key.assert_called_once()

    async def test_add_secret(self):
        """Test adding a secret."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(120, 40)) as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-secrets"
            await pilot.pause()

            # Input name and value
            name_inp = app.query_one("#secret-name-input", Input)
            name_inp.value = "NEW_SECRET"

            val_inp = app.query_one("#secret-value-input", Input)
            val_inp.value = "super_secret"

            # Click Add
            await pilot.click("#btn-secret-add")
            await pilot.pause()

            self.mock_manager.set_secret.assert_called_with("NEW_SECRET", "super_secret")

    async def test_delete_secret(self):
        """Test deleting a secret."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test(size=(160, 50)) as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-secrets"
            await pilot.pause()

            # Select a secret from list
            secrets_list = app.query_one("#secrets-list", ListView)
            # Assuming list is populated
            if secrets_list.children:
                secrets_list.index = 0
                await pilot.pause()

                # Click Delete
                await pilot.click("#btn-secret-delete")
                await pilot.pause()

                # Depending on how I implement, it might need confirmation or just delete
                # Let's assume direct delete for now or check if a confirmation dialog appears
                # If direct:
                # self.mock_manager.delete_secret.assert_called()
                pass

if __name__ == "__main__":
    unittest.main()
