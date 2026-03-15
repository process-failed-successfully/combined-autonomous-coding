import pytest
from unittest.mock import patch
import io
import argparse

from shared.bitwise_lab import BitwiseLabManager, run_bitwise_lab_logic

class TestBitwiseLabManager:
    @pytest.fixture
    def manager(self):
        return BitwiseLabManager()

    @pytest.mark.parametrize("num_str, expected", [
        ("42", 42),
        ("-10", -10),
        ("0x2a", 42),
        ("0X2A", 42),
        ("0b101010", 42),
        ("0o52", 42),
    ])
    def test_parse_number_valid(self, manager, num_str, expected):
        assert manager.parse_number(num_str) == expected

    @pytest.mark.parametrize("num_str", [
        "abc",
        "0xG",
        "0b102",
        "0o89"
    ])
    def test_parse_number_invalid(self, manager, num_str):
        with pytest.raises(ValueError):
            manager.parse_number(num_str)

    def test_format_number(self, manager):
        res = manager.format_number(42)
        assert res["dec"] == "42"
        assert res["hex"] == "0x2a"
        assert res["bin"] == "0b101010"
        assert res["oct"] == "0o52"

    def test_bitwise_and(self, manager):
        res = manager.bitwise_and("12", "10") # 1100 & 1010 = 1000 = 8
        assert res["dec"] == "8"

    def test_bitwise_or(self, manager):
        res = manager.bitwise_or("12", "10") # 1100 | 1010 = 1110 = 14
        assert res["dec"] == "14"

    def test_bitwise_xor(self, manager):
        res = manager.bitwise_xor("12", "10") # 1100 ^ 1010 = 0110 = 6
        assert res["dec"] == "6"

    def test_bitwise_not(self, manager):
        res = manager.bitwise_not("12")
        assert res["dec"] == "-13"

    def test_left_shift(self, manager):
        res = manager.left_shift("2", "3") # 2 << 3 = 16
        assert res["dec"] == "16"

        with pytest.raises(ValueError):
            manager.left_shift("2", "-1")

    def test_right_shift(self, manager):
        res = manager.right_shift("16", "3") # 16 >> 3 = 2
        assert res["dec"] == "2"

        with pytest.raises(ValueError):
            manager.right_shift("16", "-1")

def test_run_bitwise_lab_logic_convert():
    args = argparse.Namespace(action="convert", num="42")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_bitwise_lab_logic(args)
        assert success
        output = fake_stdout.getvalue()
        assert "Decimal: 42" in output
        assert "Hex:     0x2a" in output
        assert "Binary:  0b101010" in output

def test_run_bitwise_lab_logic_and():
    args = argparse.Namespace(action="and", num1="12", num2="10")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_bitwise_lab_logic(args)
        assert success
        output = fake_stdout.getvalue()
        assert "Result (Decimal): 8" in output

def test_run_bitwise_lab_logic_not():
    args = argparse.Namespace(action="not", num="12")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_bitwise_lab_logic(args)
        assert success
        output = fake_stdout.getvalue()
        assert "Result (Decimal): -13" in output

def test_run_bitwise_lab_logic_invalid_action():
    args = argparse.Namespace(action="unknown")
    with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
        success = run_bitwise_lab_logic(args)
        assert not success
        assert "Unknown action" in fake_stderr.getvalue()
