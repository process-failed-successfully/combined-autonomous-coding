import pytest
import argparse
from shared.cuid2_lab import Cuid2LabManager, run_cuid2_lab_logic, HAS_CUID2

pytestmark = pytest.mark.skipif(not HAS_CUID2, reason="cuid2 library not installed")

def test_cuid2_manager_init():
    manager = Cuid2LabManager()
    assert manager is not None

def test_cuid2_manager_generate():
    manager = Cuid2LabManager()
    results = manager.generate(count=1, length=24)
    assert len(results) == 1
    assert len(results[0]) == 24

def test_cuid2_manager_generate_multiple():
    manager = Cuid2LabManager()
    results = manager.generate(count=5, length=12)
    assert len(results) == 5
    for res in results:
        assert len(res) == 12

def test_run_cuid2_lab_logic_generate(capsys):
    args = argparse.Namespace(action="generate", count=2, length=10)
    result = run_cuid2_lab_logic(args)
    assert result is True

    captured = capsys.readouterr()
    lines = [line.strip() for line in captured.out.strip().split("\n")]
    assert len(lines) == 2
    assert len(lines[0]) == 10
    assert len(lines[1]) == 10
