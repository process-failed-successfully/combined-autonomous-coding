import pytest
from unittest.mock import MagicMock, patch
from shared.hashids_lab import HashidsLabManager, run_hashids_lab_logic, HAS_HASHIDS

pytestmark = pytest.mark.skipif(not HAS_HASHIDS, reason="hashids library not installed")

@pytest.fixture
def basic_manager():
    return HashidsLabManager(salt="test salt")

def test_manager_init():
    manager = HashidsLabManager(salt="my salt", min_length=10, alphabet="abcdefghij1234567890")
    assert manager.hashids is not None

def test_encode(basic_manager):
    encoded = basic_manager.encode([1, 2, 3])
    assert isinstance(encoded, str)
    assert len(encoded) > 0

def test_encode_negative(basic_manager):
    with pytest.raises(ValueError, match="positive integers"):
        basic_manager.encode([-1, 2])

def test_encode_empty(basic_manager):
    with pytest.raises(ValueError, match="at least one integer"):
        basic_manager.encode([])

def test_decode(basic_manager):
    encoded = basic_manager.encode([1, 2, 3])
    decoded = basic_manager.decode(encoded)
    assert decoded == [1, 2, 3]

def test_decode_empty(basic_manager):
    with pytest.raises(ValueError, match="provide a Hashid"):
        basic_manager.decode("")

def test_cli_encode(capsys):
    args = MagicMock()
    args.action = "encode"
    args.salt = "salt"
    args.min_length = 0
    args.alphabet = ""
    args.numbers = [1, 2, 3]

    result = run_hashids_lab_logic(args)
    assert result is True
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0

def test_cli_decode(capsys):
    args = MagicMock()
    args.action = "encode"
    args.salt = "salt"
    args.min_length = 0
    args.alphabet = ""
    args.numbers = [42]

    run_hashids_lab_logic(args)
    captured = capsys.readouterr()
    encoded = captured.out.strip()

    args.action = "decode"
    args.hashid = encoded

    result = run_hashids_lab_logic(args)
    assert result is True
    captured2 = capsys.readouterr()
    assert captured2.out.strip() == "42"
