import pytest
from unittest.mock import patch, MagicMock
import sys
import argparse
from shared.ksuid_lab import KsuidLabManager, run_ksuid_lab_logic

def test_ksuid_generate():
    manager = KsuidLabManager()

    # Test generation of single KSUID
    res1 = manager.generate(count=1)
    assert len(res1) == 1
    assert len(res1[0]) == 27

    # Test generation of multiple KSUIDs
    res3 = manager.generate(count=3)
    assert len(res3) == 3
    for k in res3:
        assert len(k) == 27

def test_ksuid_inspect():
    manager = KsuidLabManager()
    k = manager.generate(count=1)[0]

    info = manager.inspect(k)
    assert info["valid"] is True
    assert info["ksuid"] == k
    assert "timestamp" in info
    assert "payload_hex" in info
    assert "timestamp_iso" in info

def test_ksuid_inspect_invalid_length():
    manager = KsuidLabManager()
    info = manager.inspect("too_short")
    assert info["valid"] is False
    assert "Invalid KSUID length" in info["error"]

@patch('sys.stdout', new_callable=MagicMock)
def test_cli_ksuid_generate(mock_stdout):
    args = argparse.Namespace(action="generate", count=2)
    run_ksuid_lab_logic(args)
    output = mock_stdout.write.call_args_list
    # Since write is called sequentially with a newline, we check for two full strings output
    assert len([call for call in output if len(call[0][0].strip()) == 27]) == 2

@patch('sys.stdout', new_callable=MagicMock)
def test_cli_ksuid_bulk(mock_stdout):
    args = argparse.Namespace(action="bulk", count=5)
    run_ksuid_lab_logic(args)
    output = mock_stdout.write.call_args_list
    # Since write is called sequentially with a newline, we check for 5 full strings output
    assert len([call for call in output if len(call[0][0].strip()) == 27]) == 5

@patch('sys.stdout', new_callable=MagicMock)
def test_cli_ksuid_inspect(mock_stdout):
    manager = KsuidLabManager()
    k = manager.generate()[0]
    args = argparse.Namespace(action="inspect", ksuid=k)

    run_ksuid_lab_logic(args)
    output = "".join([call[0][0] for call in mock_stdout.write.call_args_list])

    assert "KSUID Inspection" in output
    assert k in output
    assert "Valid:         True" in output

@patch('sys.stderr', new_callable=MagicMock)
def test_cli_ksuid_inspect_invalid(mock_stderr):
    args = argparse.Namespace(action="inspect", ksuid="short")
    with pytest.raises(SystemExit):
         run_ksuid_lab_logic(args)
    output = "".join([call[0][0] for call in mock_stderr.write.call_args_list])
    assert "Invalid KSUID length" in output
