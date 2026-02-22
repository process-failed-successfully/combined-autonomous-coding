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

def test_pack_data(struct_manager, tmp_path):
    output_file = tmp_path / "packed.bin"
    values = ["123", "hello"]

    bytes_written = struct_manager.pack_data("i5s", values, output_file)

    assert bytes_written == 9
    assert output_file.exists()
    content = output_file.read_bytes()
    assert len(content) == 9

    unpacked = struct.unpack("i5s", content)
    assert unpacked[0] == 123
    assert unpacked[1] == b"hello"

def test_pack(struct_manager, tmp_path):
    output_file = tmp_path / "packed_cli.bin"
    values = ["123", "hello"]

    with patch("shared.struct_lab.console.print") as mock_print:
        struct_manager.pack("i5s", values, output_file)

        # Verify it printed success message
        assert mock_print.called
        assert "Packed 9 bytes" in str(mock_print.call_args)

def test_unpack_data(struct_manager, tmp_path):
    input_file = tmp_path / "data.bin"
    data = struct.pack("if", 42, 2.5)
    input_file.write_bytes(data)

    unpacked = struct_manager.unpack_data("if", input_file)
    assert unpacked[0] == 42
    assert abs(unpacked[1] - 2.5) < 0.0001

def test_unpack(struct_manager, tmp_path):
    input_file = tmp_path / "data_cli.bin"
    data = struct.pack("if", 42, 2.5)
    input_file.write_bytes(data)

    with patch("shared.struct_lab.console.print") as mock_print:
        struct_manager.unpack("if", input_file)

        # Verify calls
        args_list = mock_print.call_args_list
        assert len(args_list) >= 3
        # Should print the values
        assert "42" in str(args_list[1])
        assert "2.5" in str(args_list[2])

def test_get_hex_dump(struct_manager, tmp_path):
    input_file = tmp_path / "hex.bin"
    data = b"\x00\x01\x02\x03" + b"A" * 12 + b"\xff"
    input_file.write_bytes(data)

    rows = struct_manager.get_hex_dump(input_file)
    assert len(rows) == 2
    assert rows[0]["offset"] == "00000000"
    assert "00 01 02 03" in rows[0]["hex"]
    assert rows[1]["offset"] == "00000010"
    assert "ff" in rows[1]["hex"]

def test_hex_dump(struct_manager, tmp_path):
    input_file = tmp_path / "hex_cli.bin"
    data = b"\x00\x01\x02\x03"
    input_file.write_bytes(data)

    with patch("shared.struct_lab.console.print") as mock_print:
        struct_manager.hex_dump(input_file)
        assert mock_print.called

def test_run_logic_calc(tmp_path):
    args = MagicMock()
    args.action = "calc"
    args.format = "ii"
    args.project_dir = tmp_path

    with patch("shared.struct_lab.console.print") as mock_print:
        run_struct_lab_logic(args)
        mock_print.assert_called_with("Size of 'ii': [bold]8 bytes[/bold]")
