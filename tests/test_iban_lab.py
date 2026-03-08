import pytest
from unittest.mock import patch
from shared.iban_lab import IbanManager, run_iban_lab_logic

class DummyArgs:
    def __init__(self, action, iban=None, country_code=None):
        self.action = action
        self.iban = iban
        self.country_code = country_code

def test_iban_manager_validate_valid():
    manager = IbanManager()
    gb_iban = manager.generate("GB")
    assert manager.validate(gb_iban) is True

    de_iban = manager.generate("DE")
    assert manager.validate(de_iban) is True

def test_iban_manager_validate_invalid():
    manager = IbanManager()
    gb_iban = manager.generate("GB")
    # Mess up one digit to make it invalid
    bad_iban = gb_iban[:-1] + ("0" if gb_iban[-1] != "0" else "1")
    assert manager.validate(bad_iban) is False
    assert manager.validate("INVALID") is False
    assert manager.validate("GB123") is False

def test_iban_manager_generate_invalid_country():
    manager = IbanManager()
    with pytest.raises(ValueError, match="Unsupported country code"):
        manager.generate("XX")

def test_iban_manager_parse_valid():
    manager = IbanManager()
    gb_iban = manager.generate("GB")
    parsed = manager.parse(gb_iban)
    assert parsed["is_valid"] is True
    assert parsed["country_code"] == "GB"
    assert parsed["iban"] == gb_iban

def test_iban_manager_parse_invalid():
    manager = IbanManager()
    with pytest.raises(ValueError, match="Invalid IBAN length"):
        manager.parse("SHORT")

@patch('sys.exit')
@patch('builtins.print')
def test_run_iban_lab_logic_validate(mock_print, mock_exit):
    manager = IbanManager()
    valid_iban = manager.generate("FR")
    args = DummyArgs(action="validate", iban=valid_iban)
    run_iban_lab_logic(args)
    mock_exit.assert_called_with(0)

@patch('sys.exit')
@patch('builtins.print')
def test_run_iban_lab_logic_validate_invalid(mock_print, mock_exit):
    args = DummyArgs(action="validate", iban="INVALID")
    run_iban_lab_logic(args)
    mock_exit.assert_called_with(1)

@patch('sys.exit')
@patch('builtins.print')
def test_run_iban_lab_logic_generate(mock_print, mock_exit):
    args = DummyArgs(action="generate", country_code="IT")
    run_iban_lab_logic(args)
    mock_exit.assert_called_with(0)

@patch('sys.exit')
@patch('builtins.print')
def test_run_iban_lab_logic_parse(mock_print, mock_exit):
    manager = IbanManager()
    valid_iban = manager.generate("GB")
    args = DummyArgs(action="parse", iban=valid_iban)
    run_iban_lab_logic(args)
    mock_exit.assert_called_with(0)
