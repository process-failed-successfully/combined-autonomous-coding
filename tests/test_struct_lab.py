import pytest
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.struct_lab import StructLabManager, run_struct_lab_logic

@pytest.fixture
def struct_manager(tmp_path):
    return StructLabManager(tmp_path)

def test_calc_size(struct_manager):
    assert struct_manager.calc_size("i") == 4
    assert struct_manager.calc_size("2i") == 8
    assert struct_manager.calc_size("b") == 1

    with pytest.raises(ValueError):
        struct_manager.calc_size("z") # Invalid format

def test_pack(struct_manager, tmp_path):
    output_file = tmp_path / "packed.bin"

    # Pack int and bytes
    # Format 'i5s': int (4 bytes) + 5 char string (5 bytes)
    values = ["123", "hello"]
    struct_manager.pack("i5s", values, output_file)

    assert output_file.exists()
    content = output_file.read_bytes()
    assert len(content) == 9 # 4 + 5

    unpacked = struct.unpack("i5s", content)
    assert unpacked[0] == 123
    assert unpacked[1] == b"hello"

def test_pack_float(struct_manager, tmp_path):
    output_file = tmp_path / "float.bin"

    # Pack float
    values = ["3.14"]
    struct_manager.pack("f", values, output_file)

    content = output_file.read_bytes()
    assert len(content) == 4
    unpacked = struct.unpack("f", content)
    # Float precision issues
    assert abs(unpacked[0] - 3.14) < 0.0001

def test_unpack(struct_manager, tmp_path):
    input_file = tmp_path / "data.bin"
    # Create binary file: int 42, float 2.5
    data = struct.pack("if", 42, 2.5)
    input_file.write_bytes(data)

    # We need to capture the output of unpack
    with patch("shared.struct_lab.console.print") as mock_print:
        struct_manager.unpack("if", input_file)

        # Verify calls
        args_list = mock_print.call_args_list
        assert len(args_list) >= 3
        # Args list elements are (args, kwargs)
        # args_list[1][0][0] should be the string
        assert "42" in str(args_list[1])
        assert "2.5" in str(args_list[2])

def test_hex_dump(struct_manager, tmp_path):
    input_file = tmp_path / "hex.bin"
    data = b"\x00\x01\x02\x03" + b"A" * 12 + b"\xff"
    # Total 17 bytes -> 2 rows (16 + 1)
    input_file.write_bytes(data)

    with patch("shared.struct_lab.console.print") as mock_print:
        struct_manager.hex_dump(input_file)

        # Should call print with a Table
        assert mock_print.called
        table = mock_print.call_args[0][0]
        from rich.table import Table
        assert isinstance(table, Table)

def test_run_logic_calc(tmp_path):
    args = MagicMock()
    args.action = "calc"
    args.format = "ii"
    args.project_dir = tmp_path

    with patch("shared.struct_lab.console.print") as mock_print:
        run_struct_lab_logic(args)
        mock_print.assert_called_with("Size of 'ii': [bold]8 bytes[/bold]")
