import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.secrets import SecretsManager

@pytest.fixture
def secrets_manager(tmp_path):
    return SecretsManager(tmp_path)

def test_generate_key(secrets_manager):
    assert not secrets_manager.key_path.exists()
    assert secrets_manager.generate_key()
    assert secrets_manager.key_path.exists()

    # Should not overwrite by default
    assert not secrets_manager.generate_key()

    # Force overwrite
    assert secrets_manager.generate_key(force=True)

def test_load_key_from_file(secrets_manager):
    secrets_manager.generate_key()
    key = secrets_manager.load_key()
    assert key is not None
    assert len(key) > 0

def test_load_key_from_env(secrets_manager, monkeypatch):
    # Fernet key must be 32 url-safe base64-encoded bytes
    from cryptography.fernet import Fernet
    fake_key = Fernet.generate_key()
    monkeypatch.setenv("AGENT_SECRET_KEY", fake_key.decode())
    assert secrets_manager.load_key() == fake_key

def test_encryption_decryption(secrets_manager):
    secrets_manager.generate_key()

    secrets_manager.set_secret("API_KEY", "12345")

    # Verify file exists and is encrypted (not plain text)
    assert secrets_manager.secrets_path.exists()
    with open(secrets_manager.secrets_path, "rb") as f:
        content = f.read()
        assert b"12345" not in content # Should be encrypted

    # Verify decryption
    assert secrets_manager.get_secret("API_KEY") == "12345"

def test_crud_operations(secrets_manager):
    secrets_manager.generate_key()

    # Set
    secrets_manager.set_secret("A", "valA")
    secrets_manager.set_secret("B", "valB")

    # Get
    assert secrets_manager.get_secret("A") == "valA"
    assert secrets_manager.get_secret("B") == "valB"
    assert secrets_manager.get_secret("C") is None

    # List
    assert sorted(secrets_manager.list_secrets()) == ["A", "B"]

    # Delete
    assert secrets_manager.delete_secret("A")
    assert secrets_manager.get_secret("A") is None
    assert not secrets_manager.delete_secret("A") # Already deleted

def test_get_env_with_secrets(secrets_manager):
    secrets_manager.generate_key()
    secrets_manager.set_secret("TEST_SECRET", "secret_value")

    env = secrets_manager.get_env_with_secrets()
    assert env["TEST_SECRET"] == "secret_value"
    # Ensure current env is preserved
    assert "PATH" in env

def test_no_key_error(secrets_manager):
    # No key generated
    with pytest.raises(ValueError, match="Encryption key not found"):
        secrets_manager.set_secret("foo", "bar")
