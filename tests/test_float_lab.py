import pytest
from unittest.mock import patch, MagicMock
from shared.float_lab import FloatLabManager, run_float_lab_logic

def test_float_lab_encode_single():
    manager = FloatLabManager()
    res = manager.encode(-12.5, "single")
    assert res["success"] is True
    assert res["value"] == -12.5
    assert res["hex"] == "c1480000"
    assert res["sign"] == "1"
    assert res["exponent"] == "10000010"
    assert res["mantissa"] == "10010000000000000000000"

def test_float_lab_encode_double():
    manager = FloatLabManager()
    res = manager.encode(0.1, "double")
    assert res["success"] is True
    assert res["value"] == 0.1
    assert res["hex"] == "3fb999999999999a"
    assert res["sign"] == "0"
    assert res["exponent"] == "01111111011"
    assert res["mantissa"] == "1001100110011001100110011001100110011001100110011010"

def test_float_lab_decode_single():
    manager = FloatLabManager()
    res = manager.decode("c1480000", "single")
    assert res["success"] is True
    assert res["value"] == -12.5
    assert res["sign"] == "1"

def test_float_lab_decode_double():
    manager = FloatLabManager()
    res = manager.decode("3fb999999999999a", "double")
    assert res["success"] is True
    assert res["value"] == 0.1

def test_run_float_lab_logic_encode():
    args = MagicMock()
    args.action = "encode"
    args.value = -12.5
    args.precision = "single"
    with patch("builtins.print") as mock_print:
        assert run_float_lab_logic(args) is True
        mock_print.assert_any_call("Hex:       c1480000")

def test_run_float_lab_logic_decode():
    args = MagicMock()
    args.action = "decode"
    args.hex = "c1480000"
    args.precision = "single"
    with patch("builtins.print") as mock_print:
        assert run_float_lab_logic(args) is True
        mock_print.assert_any_call("Value:     -12.5")
