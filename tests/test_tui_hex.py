import unittest
import tempfile
import os
import shutil
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, DataTable, Label
from shared.tui_hex import HexTab

class HexApp(App):
    def __init__(self, project_dir: Path, hex_file: str = None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.hex_file = hex_file

    def compose(self) -> ComposeResult:
        yield HexTab(self.project_dir, hex_file=self.hex_file)

class TestHexTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.test_file = self.project_dir / "test.bin"
        self.test_file.write_bytes(b"\x12\x34\x56\x78")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    async def test_load_and_display(self):
        app = HexApp(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            file_input = app.query_one("#hex-file-input", Input)
            file_input.value = str(self.test_file)
            await pilot.click("#btn-hex-load")
            await pilot.pause()

            table = app.query_one("#hex-grid", DataTable)
            self.assertEqual(len(table.rows), 1)
            row_data = table.get_row_at(0)
            self.assertEqual(row_data[0], "00000000")
            self.assertEqual(row_data[1], "12")
            self.assertEqual(row_data[2], "34")
            self.assertEqual(row_data[3], "56")
            self.assertEqual(row_data[4], "78")

            status = app.query_one("#hex-status", Label)
            self.assertIn("Total: 4 bytes", str(status.renderable))

    async def test_auto_load_on_mount(self):
        app = HexApp(project_dir=self.project_dir, hex_file=str(self.test_file))
        async with app.run_test() as pilot:
            await pilot.pause()

            table = app.query_one("#hex-grid", DataTable)
            self.assertEqual(len(table.rows), 1)
            row_data = table.get_row_at(0)
            self.assertEqual(row_data[1], "12")
            self.assertEqual(row_data[2], "34")

    async def test_edit_and_save(self):
        app = HexApp(project_dir=self.project_dir, hex_file=str(self.test_file))
        async with app.run_test() as pilot:
            await pilot.pause()

            table = app.query_one("#hex-grid", DataTable)

            # Select the first byte (col 1)
            table.move_cursor(row=0, column=1)
            await pilot.pause()

            # Press key 'A'
            await pilot.press("A")
            await pilot.pause()

            # Press key 'B'
            await pilot.press("B")
            await pilot.pause()

            # Values are shifted left. Initially 0x12 -> A -> 0x2A -> B -> 0xAB
            # The exact logic in HexTab shifts left: new_val = ((current_byte & 0x0F) << 4) | int(char, 16)
            # Starting with 0x12:
            # Type 'A': (0x12 & 0x0F) << 4 | 0x0A => 0x02 << 4 | 0x0A => 0x20 | 0x0A => 0x2A
            # Type 'B': (0x2A & 0x0F) << 4 | 0x0B => 0x0A << 4 | 0x0B => 0xA0 | 0x0B => 0xAB

            row_data = table.get_row_at(0)
            self.assertEqual(row_data[1], "AB")

            # Save the file
            await pilot.click("#btn-hex-save")
            await pilot.pause()

            content = self.test_file.read_bytes()
            self.assertEqual(content[0], 0xAB)

if __name__ == "__main__":
    unittest.main()
