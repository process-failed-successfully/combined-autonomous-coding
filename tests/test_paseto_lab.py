import pytest
from unittest.mock import MagicMock, patch
import json
from shared.paseto_lab import PasetoManager, run_paseto_lab_logic

def test_paseto_manager_encode_decode():
    manager = PasetoManager()
    key_material = b'01234567890123456789012345678901'
    key = manager.create_key(4, 'local', key_material)

    payload = {"test": "data", "num": 123}
    footer = {"kid": "key_1"}

    token = manager.encode_token(payload, key, footer=footer)
    assert token.startswith("v4.local.")

    decoded = manager.decode_token(token, key)
    assert decoded["payload"] == payload
    assert decoded["footer"] == footer
    assert decoded["version"] == "v4"
    assert decoded["purpose"] == "local"

def test_paseto_manager_decode_no_key():
    manager = PasetoManager()
    # Structural parsing
    token = "v4.local.payload.footer"
    decoded = manager.decode_token(token)
    assert decoded["version"] == "v4"
    assert decoded["purpose"] == "local"
    assert decoded["payload"] == "payload"
    assert decoded["footer"] == "footer"

def test_paseto_manager_invalid_key():
    manager = PasetoManager()
    with pytest.raises(ValueError):
        # We can't use 'invalid_format' here because pyseto allows bytes for local keys,
        # but using a malformed PEM for 'public' will raise
        manager.create_key(4, 'public', b'invalid_pem_key_data')

def test_run_paseto_lab_logic_decode(capsys):
    args = MagicMock()
    args.action = "decode"
    args.token = "v4.local.payload"
    args.key = None

    result = run_paseto_lab_logic(args)
    assert result is True
    captured = capsys.readouterr()
    assert "Token Unverified" in captured.out

def test_run_paseto_lab_logic_sign_invalid_payload(capsys):
    args = MagicMock()
    args.action = "sign"
    args.payload = "invalid_json"

    result = run_paseto_lab_logic(args)
    assert result is False
    captured = capsys.readouterr()
    assert "Payload must be valid JSON" in captured.err
