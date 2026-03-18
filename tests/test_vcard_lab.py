import pytest
from unittest.mock import MagicMock, patch
from shared.vcard_lab import VCardManager, run_vcard_lab_logic
import sys

def test_vcard_generate():
    manager = VCardManager()
    result = manager.generate("Jane", "Doe", email="jane@test.com", org="ACME")
    assert "BEGIN:VCARD" in result
    assert "VERSION:3.0" in result
    assert "N:Doe;Jane;;;" in result
    assert "FN:Jane Doe" in result
    assert "ORG:ACME" in result
    assert "EMAIL;TYPE=PREF,INTERNET:jane@test.com" in result
    assert "END:VCARD" in result

def test_vcard_parse():
    manager = VCardManager()
    vcard_data = """BEGIN:VCARD
VERSION:3.0
N:Doe;John;;;
FN:John Doe
ORG:Company Inc
TITLE:Developer
TEL;TYPE=WORK,VOICE:123456789
EMAIL;TYPE=PREF,INTERNET:johndoe@test.com
URL:https://johndoe.com
END:VCARD"""

    parsed = manager.parse(vcard_data)
    assert parsed["first_name"] == "John"
    assert parsed["last_name"] == "Doe"
    assert parsed["full_name"] == "John Doe"
    assert parsed["org"] == "Company Inc"
    assert parsed["title"] == "Developer"
    assert parsed["phone"] == "123456789"
    assert parsed["email"] == "johndoe@test.com"
    assert parsed["url"] == "https://johndoe.com"
    assert parsed["version"] == "3.0"

def test_vcard_parse_invalid():
    manager = VCardManager()
    with pytest.raises(ValueError):
        manager.parse("INVALID VCARD")

def test_run_vcard_lab_generate_missing_names(capsys):
    args = MagicMock()
    args.action = "generate"
    args.first_name = None
    args.last_name = None

    assert run_vcard_lab_logic(args) is False
    captured = capsys.readouterr()
    assert "Error: At least --first-name or --last-name is required." in captured.err

@patch("sys.stdout.write")
def test_run_vcard_lab_generate_success(mock_write, capsys):
    args = MagicMock()
    args.action = "generate"
    args.first_name = "Test"
    args.last_name = "User"
    args.email = "test@example.com"
    args.phone = None
    args.org = None
    args.title = None
    args.url = None
    args.output = None

    assert run_vcard_lab_logic(args) is True

@patch("builtins.open")
def test_run_vcard_lab_parse_file_success(mock_open, capsys):
    args = MagicMock()
    args.action = "parse"
    args.file = "test.vcf"

    # Mock file read
    mock_file = MagicMock()
    mock_file.read.return_value = "BEGIN:VCARD\nVERSION:3.0\nN:Smith;Will;;;\nEND:VCARD\n"
    mock_open.return_value.__enter__.return_value = mock_file

    assert run_vcard_lab_logic(args) is True
    captured = capsys.readouterr()
    assert '"first_name": "Will"' in captured.out
    assert '"last_name": "Smith"' in captured.out

def test_run_vcard_lab_parse_empty(capsys):
    args = MagicMock()
    args.action = "parse"
    args.file = None

    with patch("sys.stdin.isatty", return_value=True):
        assert run_vcard_lab_logic(args) is False
        captured = capsys.readouterr()
        assert "Error: Provide a vCard via stdin or --file." in captured.err

def test_run_vcard_lab_parse_invalid_file(capsys):
    args = MagicMock()
    args.action = "parse"
    args.file = "test.vcf"

    with patch("builtins.open", side_effect=IOError("Mock error")):
        assert run_vcard_lab_logic(args) is False
        captured = capsys.readouterr()
        assert "Error reading file" in captured.err
