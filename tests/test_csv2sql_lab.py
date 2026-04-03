import unittest
from unittest.mock import MagicMock, patch
import argparse
import io
from shared.csv2sql_lab import Csv2SqlManager, run_csv2sql_lab_logic


class TestCsv2SqlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2SqlManager()

    def test_infer_value(self):
        self.assertEqual(self.manager._infer_value(""), "NULL")
        self.assertEqual(self.manager._infer_value("null"), "NULL")
        self.assertEqual(self.manager._infer_value("None"), "NULL")
        self.assertEqual(self.manager._infer_value("123"), "123")
        self.assertEqual(self.manager._infer_value("-456"), "-456")
        self.assertEqual(self.manager._infer_value("3.14"), "3.14")
        self.assertEqual(self.manager._infer_value("-0.5"), "-0.5")
        self.assertEqual(self.manager._infer_value("true"), "TRUE")
        self.assertEqual(self.manager._infer_value("false"), "FALSE")
        self.assertEqual(self.manager._infer_value("t"), "TRUE")
        self.assertEqual(self.manager._infer_value("f"), "FALSE")
        self.assertEqual(self.manager._infer_value("hello"), "'hello'")
        self.assertEqual(self.manager._infer_value("O'Connor"), "'O''Connor'")

    def test_convert_to_sql_basic(self):
        csv_data = "id,name,active,score\n1,Alice,true,95.5\n2,Bob,false,80"
        expected = (
            "INSERT INTO my_table (\"id\", \"name\", \"active\", \"score\") VALUES (1, 'Alice', TRUE, 95.5);\n"
            "INSERT INTO my_table (\"id\", \"name\", \"active\", \"score\") VALUES (2, 'Bob', FALSE, 80);"
        )
        sql = self.manager.convert_to_sql(csv_data)
        self.assertEqual(sql, expected)

    def test_convert_to_sql_empty(self):
        self.assertEqual(self.manager.convert_to_sql(""), "-- No data provided.")
        self.assertEqual(self.manager.convert_to_sql("\n   \n"), "-- No data provided.")

    def test_convert_to_sql_custom_table_delim(self):
        csv_data = "id|name\n1|Alice"
        expected = "INSERT INTO users (\"id\", \"name\") VALUES (1, 'Alice');"
        sql = self.manager.convert_to_sql(csv_data, table_name="users", delimiter="|")
        self.assertEqual(sql, expected)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_csv2sql_lab_logic_text(self, mock_stdout):
        args = argparse.Namespace(text="id,val\n1,A", table="test", delimiter=",", action="c2s", tui=False)
        success = run_csv2sql_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("INSERT INTO test (\"id\", \"val\") VALUES (1, 'A');", mock_stdout.getvalue())

    def test_run_csv2sql_lab_logic_tui(self):
        args = argparse.Namespace(action="tui", tui=True)
        success = run_csv2sql_lab_logic(args)
        self.assertTrue(success)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_csv2sql_lab_logic_file(self, mock_stdout):
        import tempfile
        import os
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write("id,val\n1,A")

        args = argparse.Namespace(file=path, table="test", delimiter=",", action="c2s", tui=False)
        success = run_csv2sql_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("INSERT INTO test (\"id\", \"val\") VALUES (1, 'A');", mock_stdout.getvalue())
        os.remove(path)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_csv2sql_lab_logic_file_error(self, mock_stderr):
        args = argparse.Namespace(file="/non/existent/file.csv", table="test", delimiter=",", action="c2s", tui=False)
        success = run_csv2sql_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error reading file:", mock_stderr.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_csv2sql_lab_logic_output(self, mock_stdout):
        import tempfile
        import os
        fd, path = tempfile.mkstemp()
        os.close(fd)

        args = argparse.Namespace(text="id,val\n1,A", table="test", delimiter=",", output=path, action="c2s", tui=False)
        success = run_csv2sql_lab_logic(args)
        self.assertTrue(success)
        with open(path, "r") as f:
            self.assertIn("INSERT INTO test (\"id\", \"val\") VALUES (1, 'A');", f.read())
        os.remove(path)


class TestCsv2SqlTab(unittest.TestCase):
    @patch("shared.tui_csv2sql.Csv2SqlManager")
    def test_csv2sql_tab_submit(self, MockCsv2SqlManager):
        from shared.tui_csv2sql import Csv2SqlTab
        from textual.widgets import TextArea, Input
        tab = Csv2SqlTab()

        mock_manager = MockCsv2SqlManager.return_value
        mock_manager.convert_to_sql.return_value = "fake_sql"

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "id,val\n1,hello"

        mock_table = MagicMock(spec=Input)
        mock_table.value = "my_table"

        mock_delim = MagicMock(spec=Input)
        mock_delim.value = ","

        mock_output = MagicMock(spec=TextArea)

        def mock_query_one(selector, type=None):
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=mock_query_one)
        tab.notify = MagicMock()

        tab.convert()

        mock_manager.convert_to_sql.assert_called_once_with("id,val\n1,hello", table_name="my_table", delimiter=",")
        self.assertEqual(mock_output.text, "fake_sql")

    @patch("shared.tui_csv2sql.Csv2SqlManager")
    def test_csv2sql_tab_empty(self, MockCsv2SqlManager):
        from shared.tui_csv2sql import Csv2SqlTab
        from textual.widgets import TextArea, Input
        tab = Csv2SqlTab()

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "   \n  "

        mock_table = MagicMock(spec=Input)
        mock_table.value = ""

        mock_delim = MagicMock(spec=Input)
        mock_delim.value = ""

        mock_output = MagicMock(spec=TextArea)

        def mock_query_one(selector, type=None):
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=mock_query_one)
        tab.notify = MagicMock()

        tab.convert()

        tab.notify.assert_called_once_with("Input CSV required.", severity="error")

    @patch("shared.tui_csv2sql.Csv2SqlManager")
    def test_csv2sql_tab_error(self, MockCsv2SqlManager):
        from shared.tui_csv2sql import Csv2SqlTab
        from textual.widgets import TextArea, Input
        tab = Csv2SqlTab()

        mock_manager = MockCsv2SqlManager.return_value
        mock_manager.convert_to_sql.side_effect = ValueError("fake error")

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "id,val\n1,hello"

        mock_table = MagicMock(spec=Input)
        mock_table.value = "my_table"

        mock_delim = MagicMock(spec=Input)
        mock_delim.value = ","

        mock_output = MagicMock(spec=TextArea)

        def mock_query_one(selector, type=None):
            if selector == "#c2s-input":
                return mock_input
            if selector == "#c2s-table-input":
                return mock_table
            if selector == "#c2s-delim-input":
                return mock_delim
            if selector == "#c2s-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=mock_query_one)
        tab.notify = MagicMock()

        tab.convert()

        tab.notify.assert_called_once_with("Error: fake error", severity="error")
        self.assertEqual(mock_output.text, "-- Error: fake error")


class TestCsv2SqlTabAsync(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_csv2sql.Csv2SqlTab.convert")
    async def test_on_button_pressed(self, mock_convert):
        from shared.tui_csv2sql import Csv2SqlTab
        from textual.widgets import Button
        tab = Csv2SqlTab()

        mock_button = MagicMock(spec=Button)
        mock_button.id = "btn-convert-c2s"
        mock_event = MagicMock(spec=Button.Pressed)
        mock_event.button = mock_button

        await tab.on_button_pressed(mock_event)
        mock_convert.assert_called_once()

    async def test_compose(self):
        from shared.tui_csv2sql import Csv2SqlTab
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield Csv2SqlTab()

        app = TestApp()
        async with app.run_test():
            tab = app.query_one(Csv2SqlTab)
            self.assertTrue(tab)
