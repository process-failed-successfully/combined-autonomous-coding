import sys
import os
sys.path.append(os.getcwd())

import unittest  # noqa: E402
from unittest.mock import patch  # noqa: E402
from textual.app import App, ComposeResult  # noqa: E402
from shared.tui_ssh import SshLabTab  # noqa: E402


class SshLabApp(App):
    def compose(self) -> ComposeResult:
        yield SshLabTab()


class TestSshLabTab(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_ssh.SshLabManager")
    async def test_mount(self, MockManager):
        # Setup mock manager
        mock_manager = MockManager.return_value
        mock_manager.list_keys.return_value = [{"name": "id_rsa", "path": "/path/id_rsa", "has_pub": True}]
        mock_manager.list_hosts.return_value = [{"Host": "myserver"}]

        app = SshLabApp()
        async with app.run_test() as pilot:
            # Check if widgets exist
            self.assertTrue(pilot.app.query_one("SshLabTab"))
            self.assertTrue(pilot.app.query_one("#ssh-keys-table"))
            self.assertTrue(pilot.app.query_one("#ssh-hosts-table"))

            # Check data loading
            mock_manager.list_keys.assert_called()
            mock_manager.list_hosts.assert_called()

            # Verify table content
            keys_table = pilot.app.query_one("#ssh-keys-table")
            self.assertEqual(keys_table.row_count, 1)


if __name__ == "__main__":
    unittest.main()
