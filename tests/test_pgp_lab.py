import pytest
from shared.pgp_lab import PGPLabManager
import tempfile
import os

@pytest.fixture
def pgp_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PGPLabManager(gnupghome=tmpdir)
        yield manager

def test_generate_key(pgp_manager):
    fingerprint = pgp_manager.generate_key("Test User", "test@example.com", "secret", key_type="RSA", key_length=1024)
    assert fingerprint is not None
    assert len(fingerprint) > 0

def test_encrypt_decrypt(pgp_manager):
    # Generate key first
    fingerprint = pgp_manager.generate_key("Test User", "test@example.com", "secret", key_type="RSA", key_length=1024)
    assert fingerprint is not None

    data = "This is a secret message."
    encrypted = pgp_manager.encrypt(data, [fingerprint])
    assert encrypted is not None
    assert "BEGIN PGP MESSAGE" in encrypted

    decrypted = pgp_manager.decrypt(encrypted, "secret")
    assert decrypted is not None
    assert decrypted == data

def test_sign_verify(pgp_manager):
    # Generate key
    fingerprint = pgp_manager.generate_key("Test User", "test@example.com", "secret", key_type="RSA", key_length=1024)
    assert fingerprint is not None

    data = "This is a message to sign."
    signed = pgp_manager.sign(data, fingerprint, "secret")
    assert signed is not None
    assert "BEGIN PGP SIGNED MESSAGE" in signed

    verified_fingerprint = pgp_manager.verify(signed)
    assert verified_fingerprint is not None
    assert verified_fingerprint == fingerprint

def test_list_keys(pgp_manager):
    keys = pgp_manager.list_keys()
    assert isinstance(keys, list)
    assert len(keys) == 0

    pgp_manager.generate_key("Test User", "test@example.com", "secret", key_type="RSA", key_length=1024)
    keys_after = pgp_manager.list_keys()
    assert len(keys_after) > 0
