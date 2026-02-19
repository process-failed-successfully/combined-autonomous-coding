import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_csv import CsvLabTab

class TestCsvLabTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

        # Patch sys.modules to mock textual before import if needed,
        # but here we already imported CsvLabTab which imports textual.
        # We rely on mocking the instance attributes.

        self.tab = CsvLabTab(self.project_dir)
        self.tab.manager = MagicMock()
        self.tab.notify = MagicMock()

        # Mock query_one
        self.mock_widgets = {}
        def get_widget(selector, type=None):
            if selector not in self.mock_widgets:
                self.mock_widgets[selector] = MagicMock()
            return self.mock_widgets[selector]

        self.tab.query_one = MagicMock(side_effect=get_widget)

    def test_load_file_success(self):
        path = Path("test.csv")
        data = [{"col1": "val1", "col2": "val2"}]
        self.tab.manager.load_csv.return_value = data
        self.tab.manager.get_headers.return_value = ["col1", "col2"]

        self.tab.load_file(path)

        self.tab.manager.load_csv.assert_called_with(path)
        self.assertEqual(self.tab.current_data, data)
        self.assertEqual(self.tab.current_headers, ["col1", "col2"])

        # Verify UI updates
        self.tab.query_one("#lbl-csv-file").update.assert_called()
        self.tab.query_one("#csv-table").clear.assert_called()
        self.tab.query_one("#csv-table").add_column.assert_any_call("col1", key="col1")
        self.tab.query_one("#csv-table").add_row.assert_called()

    def test_update_cell(self):
        # Setup
        self.tab.current_data = [{"col1": "old"}]
        self.tab.selected_cell = ("0", "col1")

        # Mock input
        self.tab.query_one("#csv-cell-input").value = "new"

        # Action
        self.tab.on_update_cell()

        # Assert
        self.assertEqual(self.tab.current_data[0]["col1"], "new")
        self.tab.query_one("#csv-table").update_cell.assert_called_with("0", "col1", "new")

    def test_add_row(self):
        # Setup
        self.tab.current_headers = ["col1"]
        self.tab.current_data = []

        # Action
        self.tab.on_add_row()

        # Assert
        self.assertEqual(len(self.tab.current_data), 1)
        self.assertEqual(self.tab.current_data[0], {"col1": ""})
        self.tab.query_one("#csv-table").add_row.assert_called()

    def test_delete_row(self):
        # Setup
        self.tab.current_data = [{"col1": "val1"}, {"col1": "val2"}]
        self.tab.selected_cell = ("0", "col1")
        self.tab.current_headers = ["col1"]

        # Action
        self.tab.on_del_row()

        # Assert
        self.assertEqual(len(self.tab.current_data), 1)
        self.assertEqual(self.tab.current_data[0]["col1"], "val2")
        self.assertIsNone(self.tab.selected_cell)

    def test_save_file(self):
        # Setup
        self.tab.current_file = Path("test.csv")
        self.tab.current_data = [{"col1": "val1"}]

        # Action
        self.tab.on_save()

        # Assert
        self.tab.manager.save_csv.assert_called_with(self.tab.current_data, Path("test.csv"))

if __name__ == "__main__":
    unittest.main()
