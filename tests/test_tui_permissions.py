import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Checkbox, Label
from shared.tui_permissions import PermissionsLabTab

class TestPermissionsLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_permissions.PermissionsManager")
        self.MockManager = self.patcher.start()

        self.tab = PermissionsLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_recalculate_from_checkboxes(self):
        # Persistent mocks
        mocks = {}
        def persistent_query(selector, type=None):
            if selector not in mocks:
                if "chk-" in selector:
                    mocks[selector] = MagicMock(spec=Checkbox)
                elif "input-" in selector:
                    mocks[selector] = MagicMock(spec=Input)
                else:
                    mocks[selector] = MagicMock()
            return mocks[selector]

        self.tab.query_one.side_effect = persistent_query

        # Initialize mocks via query_one and set values
        self.tab.query_one("#chk-u-r").value = True
        self.tab.query_one("#chk-u-w").value = True
        self.tab.query_one("#chk-u-x").value = True

        self.tab.query_one("#chk-g-r").value = True
        self.tab.query_one("#chk-g-w").value = False
        self.tab.query_one("#chk-g-x").value = True

        self.tab.query_one("#chk-o-r").value = True
        self.tab.query_one("#chk-o-w").value = False
        self.tab.query_one("#chk-o-x").value = True

        self.mock_manager.to_octal.side_effect = [7, 5, 5]
        self.mock_manager.to_symbolic.side_effect = ["rwx", "r-x", "r-x"]

        # Run
        self.tab.recalculate_from_checkboxes()

        self.assertEqual(mocks["#input-perm-octal"].value, "755")
        self.assertEqual(mocks["#input-perm-symbolic"].value, "rwxr-xr-x")

    async def test_load_file_success(self):
        mocks = {}
        def persistent_query(selector, type=None):
            if selector not in mocks:
                mocks[selector] = MagicMock()
            return mocks[selector]
        self.tab.query_one.side_effect = persistent_query

        self.tab.query_one("#input-perm-path").value = "/tmp/test"

        self.mock_manager.get_permissions.return_value = {
            "octal": "644",
            "symbolic": "rw-r--r--"
        }

        self.tab.on_load_file()

        # Input sanitization expects relative path
        self.mock_manager.get_permissions.assert_called_with("tmp/test")
        self.assertEqual(mocks["#input-perm-octal"].value, "644")
        self.assertEqual(mocks["#input-perm-symbolic"].value, "rw-r--r--")

    async def test_apply_file_success(self):
        mocks = {}
        def persistent_query(selector, type=None):
            if selector not in mocks:
                mocks[selector] = MagicMock()
            return mocks[selector]
        self.tab.query_one.side_effect = persistent_query

        self.tab.query_one("#input-perm-path").value = "/tmp/test"
        self.tab.query_one("#input-perm-octal").value = "777"

        self.mock_manager.set_permissions.return_value = True

        self.tab.on_apply_file()

        # Input sanitization expects relative path
        self.mock_manager.set_permissions.assert_called_with("tmp/test", "777")
        self.tab.notify.assert_called()

if __name__ == "__main__":
    unittest.main()
