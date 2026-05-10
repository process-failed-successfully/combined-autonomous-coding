import pytest
from shared.phonetic_lab import PhoneticLabManager

def test_soundex_basic():
    manager = PhoneticLabManager()
    assert manager.soundex("Robert") == "R163"
    assert manager.soundex("Rupert") == "R163"
    assert manager.soundex("Rubin") == "R150"

def test_soundex_consecutive_consonants():
    manager = PhoneticLabManager()
    # P and F map to 1. Since they are consecutive, they are coded as a single 1.
    assert manager.soundex("Pfister") == "P236"
    assert manager.soundex("Tymczak") == "T522"

def test_soundex_h_and_w():
    manager = PhoneticLabManager()
    assert manager.soundex("Ashcraft") == "A261"

def test_soundex_empty_and_special():
    manager = PhoneticLabManager()
    assert manager.soundex("") == ""
    assert manager.soundex("  ") == ""
    assert manager.soundex("123!") == ""

def test_soundex_multiple_words():
    manager = PhoneticLabManager()
    assert manager.soundex("Robert Pfister") == "R163 P236"

def test_soundex_padding():
    manager = PhoneticLabManager()
    assert manager.soundex("A") == "A000"
    assert manager.soundex("Bo") == "B000"
