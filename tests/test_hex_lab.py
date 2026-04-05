import unittest
import tempfile
import os
import sys
import shutil
from pathlib import Path
from shared.hex_lab import HexManager

class TestHexManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = HexManager(Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_and_read(self):
        # Create dummy file
        file_path = Path(self.temp_dir) / "test.bin"
        file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        self.manager.load_file(file_path)
        self.assertEqual(self.manager.get_size(), 6)

        chunk = self.manager.read_chunk(0, 4)
        self.assertEqual(chunk, b"\x00\x01\x02\x03")

        chunk = self.manager.read_chunk(4, 4)
        self.assertEqual(chunk, b"\x04\x05")

    def test_write_and_save(self):
        file_path = Path(self.temp_dir) / "test.bin"
        file_path.write_bytes(b"\x00\x00\x00")

        self.manager.load_file(file_path)
        self.manager.write_byte(1, 0xFF)

        # Check in memory
        self.assertEqual(self.manager.read_chunk(0, 3), b"\x00\xFF\x00")

        # Save
        self.manager.save_file()

        # Check on disk
        content = file_path.read_bytes()
        self.assertEqual(content, b"\x00\xFF\x00")

    def test_large_file_limit(self):
        file_path = Path(self.temp_dir) / "large.bin"
        # 11 MB
        with open(file_path, "wb") as f:
            f.seek(11 * 1024 * 1024 - 1)
            f.write(b"\0")

        with self.assertRaises(ValueError):
            self.manager.load_file(file_path)

    def test_dump_logic(self):
        file_path = Path(self.temp_dir) / "test_dump.bin"
        file_path.write_bytes(b"Hello World!....\x01\x02\x03\x04")

        self.manager.load_file(file_path)
        output = self.manager.dump()

        expected_output = (
            "00000000: 48 65 6C 6C 6F 20 57 6F  72 6C 64 21 2E 2E 2E 2E |Hello World!....|\n"
            "00000010: 01 02 03 04                                      |....|"
        )
        self.assertEqual(output, expected_output)

    def test_dump_with_offset_and_length(self):
        file_path = Path(self.temp_dir) / "test_dump2.bin"
        file_path.write_bytes(b"Hello World!....\x01\x02\x03\x04")
        self.manager.load_file(file_path)

        output = self.manager.dump(offset=6, length=5)
        # Should just be "World"
        expected_output = "00000006: 57 6F 72 6C 64                                   |World|"
        self.assertEqual(output, expected_output)


import io
import argparse
from unittest.mock import patch, MagicMock

from shared.hex_lab import run_hex_lab_logic

class TestHexLabCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_hex_lab_logic_dump(self, mock_stdout):
        file_path = Path(self.temp_dir) / "test.bin"
        file_path.write_bytes(b"ABC")

        args = argparse.Namespace(
            action="dump",
            file=str(file_path),
            offset=0,
            length=None,
            project_dir=Path(self.temp_dir)
        )

        with self.assertRaises(SystemExit) as cm:
            run_hex_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("00000000: 41 42 43", mock_stdout.getvalue())

    @patch('asyncio.get_running_loop')
    def test_run_hex_lab_logic_tui(self, mock_get_loop):
        import sys
        mock_tui_module = MagicMock()
        mock_tui = MagicMock()
        mock_app = MagicMock()
        mock_tui.return_value = mock_app
        mock_tui_module.AgentTUI = mock_tui

        sys.modules['shared.tui'] = mock_tui_module

        mock_get_loop.side_effect = RuntimeError('no loop')

        args = argparse.Namespace(
            action="tui",
            file="foo.bin",
            project_dir=Path(self.temp_dir)
        )

        run_hex_lab_logic(args)

        mock_tui.assert_called_once_with(project_dir=args.project_dir, start_tab="tab-hex", hex_file="foo.bin")
        mock_app.run.assert_called_once()

        # Cleanup
        del sys.modules['shared.tui']

if __name__ == '__main__':
    unittest.main()
