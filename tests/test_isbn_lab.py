import pytest
from unittest.mock import patch
from shared.isbn_lab import IsbnManager, run_isbn_lab_logic

class DummyArgs:
    def __init__(self, action, isbn=None, format=None, prefix=None):
        self.action = action
        self.isbn = isbn
        self.format = format
        self.prefix = prefix

def test_validate_isbn10_valid():
    manager = IsbnManager()
    assert manager.validate("0-306-40615-2") is True
    assert manager.validate("0306406152") is True
    assert manager.validate("0-13-110362-8") is True
    assert manager.validate("0-684-84328-5") is True
    assert manager.validate("0-8044-2957-X") is True
    assert manager.validate("080442957X") is True

def test_validate_isbn10_invalid():
    manager = IsbnManager()
    assert manager.validate("0-306-40615-3") is False # Bad check digit
    assert manager.validate("0-306-4061-2") is False  # Too short
    assert manager.validate("123456789") is False

def test_validate_isbn13_valid():
    manager = IsbnManager()
    assert manager.validate("978-0-306-40615-7") is True
    assert manager.validate("9780306406157") is True
    assert manager.validate("978-3-16-148410-0") is True
    assert manager.validate("979-10-90636-07-1") is True

def test_validate_isbn13_invalid():
    manager = IsbnManager()
    assert manager.validate("978-0-306-40615-8") is False # Bad check digit
    assert manager.validate("978-0-306-4061") is False    # Too short
    assert manager.validate("1234567890123") is False

def test_generate_isbn10():
    manager = IsbnManager()
    isbn = manager.generate(format_type="10")
    assert len(isbn) == 10
    assert manager.validate(isbn) is True

def test_generate_isbn13():
    manager = IsbnManager()
    isbn = manager.generate(format_type="13", prefix="978")
    assert len(isbn) == 13
    assert isbn.startswith("978")
    assert manager.validate(isbn) is True

    isbn2 = manager.generate(format_type="13", prefix="979")
    assert isbn2.startswith("979")
    assert manager.validate(isbn2) is True

def test_generate_invalid_format():
    manager = IsbnManager()
    with pytest.raises(ValueError):
        manager.generate(format_type="12")

def test_parse_isbn10():
    manager = IsbnManager()
    parsed = manager.parse("0-306-40615-2")
    assert parsed["is_valid"] is True
    assert parsed["format"] == "ISBN-10"
    assert parsed["clean_isbn"] == "0306406152"
    assert parsed["checksum"] == "2"

def test_parse_isbn13():
    manager = IsbnManager()
    parsed = manager.parse("978-0-306-40615-7")
    assert parsed["is_valid"] is True
    assert parsed["format"] == "ISBN-13"
    assert parsed["clean_isbn"] == "9780306406157"
    assert parsed["prefix"] == "978"
    assert parsed["checksum"] == "7"

def test_parse_invalid():
    manager = IsbnManager()
    with pytest.raises(ValueError, match="Invalid ISBN length"):
        manager.parse("123")

def test_convert_isbn10_to_13():
    manager = IsbnManager()
    isbn13 = manager.convert("0-306-40615-2")
    assert isbn13 == "9780306406157"
    assert manager.validate(isbn13) is True

    with pytest.raises(ValueError):
        manager.convert("0-306-40615-3") # Invalid ISBN-10

    with pytest.raises(ValueError):
        manager.convert("123") # Invalid length

@patch('sys.exit')
@patch('builtins.print')
def test_run_isbn_lab_logic_validate(mock_print, mock_exit):
    args = DummyArgs(action="validate", isbn="0-306-40615-2")
    run_isbn_lab_logic(args)
    mock_exit.assert_called_with(0)
    mock_print.assert_called_with("✅ The ISBN '0-306-40615-2' is valid.")

@patch('sys.exit')
@patch('builtins.print')
def test_run_isbn_lab_logic_validate_invalid(mock_print, mock_exit):
    args = DummyArgs(action="validate", isbn="123")
    run_isbn_lab_logic(args)
    mock_exit.assert_called_with(1)

@patch('sys.exit')
@patch('builtins.print')
def test_run_isbn_lab_logic_generate(mock_print, mock_exit):
    args = DummyArgs(action="generate", format="13", prefix="978")
    run_isbn_lab_logic(args)
    mock_exit.assert_called_with(0)

@patch('sys.exit')
@patch('builtins.print')
def test_run_isbn_lab_logic_parse(mock_print, mock_exit):
    args = DummyArgs(action="parse", isbn="978-0-306-40615-7")
    run_isbn_lab_logic(args)
    mock_exit.assert_called_with(0)

@patch('sys.exit')
@patch('builtins.print')
def test_run_isbn_lab_logic_convert(mock_print, mock_exit):
    args = DummyArgs(action="convert", isbn="0-306-40615-2")
    run_isbn_lab_logic(args)
    mock_exit.assert_called_with(0)
    mock_print.assert_called_with("✅ Converted ISBN-10 '0-306-40615-2' to ISBN-13: 9780306406157")
