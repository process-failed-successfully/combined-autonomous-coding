import pytest
from unittest.mock import MagicMock, patch
from shared.enc_lab import EncLabManager, run_enc_lab_logic

@pytest.fixture
def manager():
    return EncLabManager()

def test_base64(manager):
    original = "Hello World"
    encoded = manager.base64_process(original)
    assert encoded == "SGVsbG8gV29ybGQ="
    decoded = manager.base64_process(encoded, decode=True)
    assert decoded == original

def test_base64_invalid(manager):
    with pytest.raises(ValueError):
        manager.base64_process("NotBase64!!!", decode=True)

def test_url(manager):
    original = "Hello World?"
    encoded = manager.url_process(original)
    assert encoded == "Hello%20World%3F"
    decoded = manager.url_process(encoded, decode=True)
    assert decoded == original

def test_html(manager):
    original = "<script>alert('xss')</script>"
    encoded = manager.html_process(original)
    assert encoded == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    decoded = manager.html_process(encoded, decode=True)
    assert decoded == original

def test_hex(manager):
    original = "Hello"
    encoded = manager.hex_process(original)
    assert encoded == "48656c6c6f"
    decoded = manager.hex_process(encoded, decode=True)
    assert decoded == original

def test_hex_with_spaces(manager):
    encoded = "48 65 6c 6c 6f"
    decoded = manager.hex_process(encoded, decode=True)
    assert decoded == "Hello"

def test_rot13(manager):
    original = "Hello"
    encoded = manager.rot13_process(original)
    assert encoded == "Uryyb"
    decoded = manager.rot13_process(encoded)
    assert decoded == original

def test_run_logic_base64(capsys):
    args = MagicMock()
    args.action = "base64"
    args.text = "Hello"
    args.decode = False

    run_enc_lab_logic(args)
    captured = capsys.readouterr()
    assert "SGVsbG8=" in captured.out

def test_run_logic_decode(capsys):
    args = MagicMock()
    args.action = "base64"
    args.text = "SGVsbG8="
    args.decode = True

    run_enc_lab_logic(args)
    captured = capsys.readouterr()
    assert "Hello" in captured.out

def test_run_logic_missing_input(capsys):
    args = MagicMock()
    args.action = "base64"
    args.text = None
    args.decode = False

    # Mock stdin to return empty string
    with patch("sys.stdin.isatty", return_value=True):
         run_enc_lab_logic(args)
         # Should verify error message printed to console
         # Since we use rich.console, it prints to stdout/stderr depending on config, but usually stdout for errors in simple scripts?
         # Actually console.print usually goes to stdout.
         # The code says console.print("[red]Error: ...")

    # We need to capture rich output. Rich detects capture and might strip colors or not.
    # Let's just check if it returns False
    with patch("sys.stdin.isatty", return_value=True):
        assert run_enc_lab_logic(args) is False
