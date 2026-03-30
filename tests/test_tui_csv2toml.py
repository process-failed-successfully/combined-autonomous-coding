import unittest
from pathlib import Path
from typing import Any
from textual.app import App, ComposeResult

from shared.tui_csv2toml import Csv2TomlTab


class DummyApp(App[Any]):
    def __init__(self, project_dir: Path, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield Csv2TomlTab(project_dir=self.project_dir)


class TestCsv2TomlTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

        # Create a test CSV file
        self.test_csv = self.project_dir / "test.csv"
        self.test_csv.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")

        self.app = DummyApp(project_dir=self.project_dir)

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_csv2toml_convert(self):
        async with self.app.run_test(size=(200, 200)) as pilot:
            tab = self.app.query_one(Csv2TomlTab)

            # Simulate file selection
            tab.load_file(self.test_csv)
            await pilot.pause()

            # Verify input area has text
            input_editor = tab.query_one("#csv2toml-input-editor")
            self.assertIn("Alice", input_editor.text)

            # Click convert
            await pilot.click("#btn-csv2toml-convert")
            await pilot.pause()

            # Verify output
            output_editor = tab.query_one("#csv2toml-output-editor")
            self.assertIn("items", output_editor.text)
            self.assertIn('name = "Alice"', output_editor.text)
            self.assertIn('age = "30"', output_editor.text)

            # Save button should be enabled
            save_btn = tab.query_one("#btn-csv2toml-save")
            self.assertFalse(save_btn.disabled)

    async def test_csv2toml_save(self):
        async with self.app.run_test(size=(200, 200)) as pilot:
            tab = self.app.query_one(Csv2TomlTab)

            # Simulate file selection and convert
            tab.load_file(self.test_csv)
            await pilot.click("#btn-csv2toml-convert")
            await pilot.pause()

            # Click save
            await pilot.click("#btn-csv2toml-save")
            await pilot.pause()

            # Verify file created
            out_file = self.test_csv.with_suffix(".toml")
            self.assertTrue(out_file.exists())
            self.assertIn("Alice", out_file.read_text(encoding="utf-8"))

    async def test_csv2toml_empty_convert(self):
        async with self.app.run_test(size=(200, 200)) as pilot:
            tab = self.app.query_one(Csv2TomlTab)

            # Set empty text
            tab.query_one("#csv2toml-input-editor").text = ""

            # Click convert
            await pilot.click("#btn-csv2toml-convert")
            await pilot.pause()

            # Output should be empty
            output_editor = tab.query_one("#csv2toml-output-editor")
            self.assertEqual(output_editor.text, "")

            # Log should indicate warning (via notification in real app, but we can check log if we added one)
            # Just ensure no crash

    async def test_csv2toml_invalid_file(self):
        async with self.app.run_test(size=(200, 200)) as pilot:
            tab = self.app.query_one(Csv2TomlTab)

            # Simulate missing file
            missing_csv = self.project_dir / "missing.csv"
            tab.load_file(missing_csv)
            await pilot.pause()

            # Check log for error
            log = tab.query_one("#csv2toml-log")
            self.assertTrue(any("Error loading CSV" in str(line) for line in log.lines))


if __name__ == "__main__":
    unittest.main()
