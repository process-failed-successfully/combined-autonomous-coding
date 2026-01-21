import shutil
import tempfile
from pathlib import Path
import pytest
from shared.secrets import SecretsManager

@pytest.fixture
def temp_project():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_encryption_decryption_flow(temp_project):
    """Test full cycle of encrypting and decrypting a file."""
    manager = SecretsManager(temp_project)

    # Create a dummy secret file
    secret_file = temp_project / ".env"
    secret_content = "API_KEY=super_secret_value\nDB_PASS=12345"
    secret_file.write_text(secret_content)

    # Encrypt
    encrypted_file = temp_project / ".env.enc"
    password = "testpassword"

    assert manager.encrypt_file(secret_file, encrypted_file, password) == True
    assert encrypted_file.exists()
    assert encrypted_file.read_bytes() != secret_content.encode()

    # Decrypt
    decrypted_file = temp_project / ".env.dec"
    assert manager.decrypt_file(encrypted_file, decrypted_file, password) == True

    assert decrypted_file.exists()
    assert decrypted_file.read_text() == secret_content

def test_encryption_wrong_password(temp_project):
    """Test that decryption fails with wrong password."""
    manager = SecretsManager(temp_project)

    secret_file = temp_project / "secret.txt"
    secret_file.write_text("content")
    encrypted_file = temp_project / "secret.txt.enc"

    manager.encrypt_file(secret_file, encrypted_file, "correct_pass")

    # Attempt decrypt with wrong pass
    assert manager.decrypt_file(encrypted_file, password="wrong_pass") == False

def test_rotate_secret(temp_project):
    """Test rotating a secret in a file."""
    manager = SecretsManager(temp_project)

    env_file = temp_project / ".env"
    env_file.write_text("OLD_KEY=old_value\nOTHER=thing")

    # Rotate existing key
    assert manager.rotate_secret(env_file, "OLD_KEY") == True

    content = env_file.read_text()
    assert "OLD_KEY=" in content
    assert "OLD_KEY=old_value" not in content
    assert "OTHER=thing" in content # Ensure other lines untouched

    # Rotate new key (add it)
    assert manager.rotate_secret(env_file, "NEW_KEY") == True
    content = env_file.read_text()
    assert "NEW_KEY=" in content

def test_audit_secrets_mock(temp_project, mocker):
    """Test the audit functionality using mocks."""
    manager = SecretsManager(temp_project)

    # Mock SecurityAuditor to verify it's called
    mocker.patch("shared.security.SecurityAuditor.scan_secrets", return_value=[
        {"description": "Fake Secret", "file": "fake.py", "line": 1, "snippet": "secret=123"}
    ])

    # This just ensures no exception is raised and logic flows
    # We can capture stdout if we want to assert output, but simple execution is a good start
    manager.audit_secrets()
