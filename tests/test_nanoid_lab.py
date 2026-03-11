import pytest
from shared.nanoid_lab import NanoIDLabManager

def test_nanoid_generate_default():
    manager = NanoIDLabManager()
    results = manager.generate()
    assert len(results) == 1
    assert len(results[0]) == 21

def test_nanoid_generate_count():
    manager = NanoIDLabManager()
    results = manager.generate(count=5)
    assert len(results) == 5

def test_nanoid_generate_custom_size():
    manager = NanoIDLabManager()
    results = manager.generate(size=10)
    assert len(results[0]) == 10

def test_nanoid_generate_custom_alphabet():
    manager = NanoIDLabManager()
    alphabet = "abc"
    results = manager.generate(alphabet=alphabet, size=5)
    for char in results[0]:
        assert char in alphabet
