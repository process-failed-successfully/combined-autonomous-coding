import pytest
import argparse
import sys
from io import StringIO
from shared.typeid_lab import TypeIDLabManager, run_typeid_lab_logic, HAS_TYPEID

pytestmark = pytest.mark.skipif(not HAS_TYPEID, reason="typeid-python library not installed")

def test_typeid_manager_init():
    manager = TypeIDLabManager()
    assert manager is not None

def test_typeid_manager_generate():
    manager = TypeIDLabManager()
    results = manager.generate(prefix="user", count=1)
    assert len(results) == 1
    assert results[0].startswith("user_")

def test_typeid_manager_generate_multiple():
    manager = TypeIDLabManager()
    results = manager.generate(prefix="test", count=3)
    assert len(results) == 3
    for res in results:
        assert res.startswith("test_")

def test_typeid_manager_generate_no_prefix():
    manager = TypeIDLabManager()
    results = manager.generate(prefix="", count=1)
    assert len(results) == 1
    assert "_" not in results[0] # Empty prefix means no underscore

def test_typeid_manager_parse_valid():
    manager = TypeIDLabManager()
    t_id = manager.generate(prefix="org", count=1)[0]
    parsed = manager.parse(t_id)
    assert parsed["valid"] is True
    assert parsed["prefix"] == "org"
    assert parsed["typeid"] == t_id
    assert "uuid" in parsed

def test_typeid_manager_parse_invalid():
    manager = TypeIDLabManager()
    parsed = manager.parse("invalid_type_id")
    assert parsed["valid"] is False
    assert "error" in parsed

def test_run_typeid_lab_logic_generate(capsys):
    args = argparse.Namespace(action="generate", prefix="user", count=2)
    result = run_typeid_lab_logic(args)
    assert result is True

    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().split("\n")]
    assert len(lines) == 2
    for line in lines:
        assert line.startswith("user_")

def test_run_typeid_lab_logic_parse(capsys):
    manager = TypeIDLabManager()
    t_id = manager.generate(prefix="account", count=1)[0]

    args = argparse.Namespace(action="parse", typeid=t_id)
    result = run_typeid_lab_logic(args)
    assert result is True

    captured = capsys.readouterr()
    assert "Valid: Yes" in captured.out
    assert "Prefix: account" in captured.out
