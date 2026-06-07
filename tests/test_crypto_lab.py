import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.crypto_lab import CryptoLabManager, run_crypto_lab_logic

@pytest.fixture
def crypto_manager():
    return CryptoLabManager()

def test_hash_data(crypto_manager):
    # Test SHA256
    input_data = "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert crypto_manager.hash_data(input_data, "sha256") == expected

    # Test MD5
    expected_md5 = "5eb63bbbe01eeed093cb22bb8f5acdc3"
    assert crypto_manager.hash_data(input_data, "md5") == expected_md5

    # Test Bytes
    assert crypto_manager.hash_data(b"hello world", "sha256") == expected

def test_pbkdf2_hmac(crypto_manager):
    password = "secret_password"
    salt = "salty_salt"

    # Pre-calculated PBKDF2 hash using pbkdf2_hmac('sha256', b'secret_password', b'salty_salt', 100000, 32).hex()
    expected = "7d9b0ca692ff57bae7513128a694833020d402c112face31e0a2849867175575"
    assert crypto_manager.pbkdf2_hmac(password, salt, "sha256", 100000, 32) == expected

    # Test Bytes
    assert crypto_manager.pbkdf2_hmac(b"secret_password", b"salty_salt", "sha256", 100000, 32) == expected

def test_hmac_data(crypto_manager):
    input_data = "hello world"
    key = "secret"
    expected = "734cc62f32841568f45715aeb9f4d7891324e6d948e4c6c60c0621cdac48623a"
    assert crypto_manager.hmac_data(input_data, key, "sha256") == expected

    # Test Bytes
    assert crypto_manager.hmac_data(b"hello world", b"secret", "sha256") == expected

def test_generate_key(crypto_manager):
    key = crypto_manager.generate_key()
    assert isinstance(key, bytes)
    assert len(key) > 0 # Fernet key length is fixed but let's just check valid bytes

def test_encrypt_decrypt(crypto_manager):
    key = crypto_manager.generate_key()
    data = "secret message"

    encrypted = crypto_manager.encrypt_data(data, key)
    assert encrypted != data.encode("utf-8")

    decrypted = crypto_manager.decrypt_data(encrypted, key)
    assert decrypted.decode("utf-8") == data

    # Test with bytes
    data_bytes = b"secret bytes"
    encrypted_bytes = crypto_manager.encrypt_data(data_bytes, key)
    decrypted_bytes = crypto_manager.decrypt_data(encrypted_bytes, key)
    assert decrypted_bytes == data_bytes

def test_generate_random(crypto_manager):
    # Hex
    rand_hex = crypto_manager.generate_random(length=10, type="hex")
    assert len(rand_hex) == 10

    # Base64
    rand_b64 = crypto_manager.generate_random(length=10, type="base64")
    assert len(rand_b64) >= 10 # Base64 might be slightly longer due to encoding

    # UUID
    rand_uuid = crypto_manager.generate_random(type="uuid")
    assert len(rand_uuid) == 36

    # Int
    rand_int = crypto_manager.generate_random(length=4, type="int")
    assert rand_int.isdigit()

def test_cli_hash(capsys):
    args = MagicMock()
    args.action = "hash"
    args.text = "test"
    args.file = None
    args.algo = "sha256"

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08" in captured.out

def test_cli_pbkdf2(capsys):
    args = MagicMock()
    args.action = "pbkdf2"
    args.password = "secret"
    args.salt = "salty"
    args.algo = "sha256"
    args.iterations = 100000
    args.dklen = 32

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    expected_hash = "2ae5b47935dccabaf61792f4394bd046d085e128ab64400f80dcb4c1364bb85c"
    assert expected_hash in captured.out

def test_cli_hmac(capsys):
    args = MagicMock()
    args.action = "hmac"
    args.text = "hello world"
    args.file = None
    args.key = "secret"
    args.key_file = None
    args.algo = "sha256"

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert "734cc62f32841568f45715aeb9f4d7891324e6d948e4c6c60c0621cdac48623a" in captured.out

def test_cli_gen_key(capsys):
    args = MagicMock()
    args.action = "gen-key"
    args.output = None

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0

def test_cli_encrypt_decrypt(tmp_path):
    # Gen Key
    manager = CryptoLabManager()
    key = manager.generate_key()
    key_file = tmp_path / "test.key"
    key_file.write_bytes(key)

    input_file = tmp_path / "input.txt"
    input_file.write_text("secret")

    enc_file = tmp_path / "enc.txt"
    dec_file = tmp_path / "dec.txt"

    # Encrypt
    args_enc = MagicMock()
    args_enc.action = "encrypt"
    args_enc.key = None
    args_enc.key_file = str(key_file)
    args_enc.input = None
    args_enc.input_file = str(input_file)
    args_enc.output = str(enc_file)

    assert run_crypto_lab_logic(args_enc)
    assert enc_file.exists()

    # Decrypt
    args_dec = MagicMock()
    args_dec.action = "decrypt"
    args_dec.key = None
    args_dec.key_file = str(key_file)
    args_dec.input = None
    args_dec.input_file = str(enc_file)
    args_dec.output = str(dec_file)

    assert run_crypto_lab_logic(args_dec)
    assert dec_file.read_text() == "secret"

def test_cli_random(capsys):
    args = MagicMock()
    args.action = "random"
    args.length = 8
    args.type = "hex"

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert len(captured.out.strip()) == 8

def test_rsa_keygen(crypto_manager):
    priv, pub = crypto_manager.generate_rsa_keypair()
    assert b"BEGIN PRIVATE KEY" in priv
    assert b"BEGIN PUBLIC KEY" in pub

def test_rsa_encrypt_decrypt(crypto_manager):
    priv, pub = crypto_manager.generate_rsa_keypair()
    test_str = "secret_data"
    encrypted = crypto_manager.rsa_encrypt(test_str, pub)
    decrypted = crypto_manager.rsa_decrypt(encrypted, priv)
    assert decrypted.decode('utf-8') == test_str

def test_rsa_sign_verify(crypto_manager):
    priv, pub = crypto_manager.generate_rsa_keypair()
    test_str = "secret_data"
    signature = crypto_manager.rsa_sign(test_str, priv)
    is_valid = crypto_manager.rsa_verify(test_str, signature, pub)
    assert is_valid

    # Test invalid signature
    is_invalid = crypto_manager.rsa_verify(test_str, b"bad_signature", pub)
    assert not is_invalid

def test_cli_rsa_keygen(capsys):
    args = MagicMock()
    args.action = "rsa-keygen"
    args.output = None

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert "BEGIN PRIVATE KEY" in captured.out
    assert "BEGIN PUBLIC KEY" in captured.out

def test_ed25519_keygen(crypto_manager):
    priv, pub = crypto_manager.generate_ed25519_keypair()
    assert b"BEGIN PRIVATE KEY" in priv
    assert b"BEGIN PUBLIC KEY" in pub

def test_ed25519_sign_verify(crypto_manager):
    priv, pub = crypto_manager.generate_ed25519_keypair()
    test_str = "secret_data"
    signature = crypto_manager.ed25519_sign(test_str, priv)

    is_valid = crypto_manager.ed25519_verify(test_str, signature, pub)
    assert is_valid

    # Test invalid signature
    is_invalid = crypto_manager.ed25519_verify(test_str, b"bad_signature_padding12345", pub)
    assert not is_invalid

def test_cli_ed25519_keygen(capsys):
    args = MagicMock()
    args.action = "ed25519-keygen"
    args.output = None

    run_crypto_lab_logic(args)
    captured = capsys.readouterr()
    assert "BEGIN PRIVATE KEY" in captured.out
    assert "BEGIN PUBLIC KEY" in captured.out
