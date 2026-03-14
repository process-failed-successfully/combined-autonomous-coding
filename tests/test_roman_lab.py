import pytest
from unittest.mock import patch
import io
import argparse

from shared.roman_lab import RomanLabManager, run_roman_lab_logic


class TestRomanLabManager:
    @pytest.fixture
    def manager(self):
        return RomanLabManager()

    @pytest.mark.parametrize("arabic, roman", [
        (1, 'I'),
        (4, 'IV'),
        (9, 'IX'),
        (42, 'XLII'),
        (99, 'XCIX'),
        (2024, 'MMXXIV'),
        (3999, 'MMMCMXCIX')
    ])
    def test_int_to_roman_valid(self, manager, arabic, roman):
        assert manager.int_to_roman(arabic) == roman

    @pytest.mark.parametrize("invalid_int", [
        0, 4000, -1, 5000
    ])
    def test_int_to_roman_invalid(self, manager, invalid_int):
        with pytest.raises(ValueError):
            manager.int_to_roman(invalid_int)

    def test_int_to_roman_type_error(self, manager):
        with pytest.raises(TypeError):
            manager.int_to_roman("10")  # type: ignore

    @pytest.mark.parametrize("roman, arabic", [
        ('I', 1),
        ('IV', 4),
        ('IX', 9),
        ('XLII', 42),
        ('XCIX', 99),
        ('MMXXIV', 2024),
        ('MMMCMXCIX', 3999),
        ('mmxxiv', 2024)  # case insensitive
    ])
    def test_roman_to_int_valid(self, manager, roman, arabic):
        assert manager.roman_to_int(roman) == arabic

    @pytest.mark.parametrize("invalid_roman", [
        "", "IIII", "IC", "XM", "VV", "A", "MMMM"
    ])
    def test_roman_to_int_invalid(self, manager, invalid_roman):
        with pytest.raises(ValueError):
            manager.roman_to_int(invalid_roman)

    def test_roman_to_int_type_error(self, manager):
        with pytest.raises(TypeError):
            manager.roman_to_int(10)  # type: ignore

    def test_convert_auto_detect(self, manager):
        success, out = manager.convert("2024")
        assert success
        assert out == "MMXXIV"

        success, out = manager.convert("MMXXIV")
        assert success
        assert out == "2024"

        success, out = manager.convert(" invalid ")
        assert not success


def test_run_roman_lab_logic_convert_value():
    args = argparse.Namespace(action="convert", value="10")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_roman_lab_logic(args)
        assert success
        assert fake_stdout.getvalue().strip() == "X"


def test_run_roman_lab_logic_convert_stdin():
    args = argparse.Namespace(action="convert", value=None)
    with patch('sys.stdin', io.StringIO("XX")), \
         patch('sys.stdin.isatty', return_value=False), \
         patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_roman_lab_logic(args)
        assert success
        assert fake_stdout.getvalue().strip() == "20"


def test_run_roman_lab_logic_invalid_action():
    args = argparse.Namespace(action="unknown", value="10")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_roman_lab_logic(args)
        assert not success
        assert "Unknown action" in fake_stdout.getvalue()


def test_run_roman_lab_logic_empty_value():
    args = argparse.Namespace(action="convert", value=None)
    with patch('sys.stdin.isatty', return_value=True), \
         patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_roman_lab_logic(args)
        assert not success
        assert "Value is required" in fake_stdout.getvalue()


def test_run_roman_lab_logic_convert_error():
    args = argparse.Namespace(action="convert", value="INVALID")
    with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
        success = run_roman_lab_logic(args)
        assert not success
        assert "Error:" in fake_stdout.getvalue()
