from shared.braille_lab import BrailleLabManager


def test_braille_encode():
    manager = BrailleLabManager()
    assert manager.encode("hello") == "⠓⠑⠇⠇⠕"
    assert manager.encode("HELLO") == "⠓⠑⠇⠇⠕"
    assert manager.encode("hello world") == "⠓⠑⠇⠇⠕ ⠺⠕⠗⠇⠙"
    assert manager.encode("123") == "⠼⠁⠼⠃⠼⠉"
    assert manager.encode("") == ""
    assert manager.encode("!") == "⠖"


def test_braille_decode():
    manager = BrailleLabManager()
    assert manager.decode("⠓⠑⠇⠇⠕") == "hello"
    assert manager.decode("⠓⠑⠇⠇⠕ ⠺⠕⠗⠇⠙") == "hello world"
    assert manager.decode("⠼⠁⠼⠃⠼⠉") == "123"
    assert manager.decode("") == ""
    assert manager.decode("⠖") == "!"


def test_braille_unknown_chars():
    manager = BrailleLabManager()
    assert manager.encode("hello @") == "⠓⠑⠇⠇⠕ @"
    assert manager.decode("⠓⠑⠇⠇⠕ @") == "hello @"
