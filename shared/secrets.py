import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from cryptography.fernet import Fernet

class SecretsManager:
    """
    Manages encrypted secrets for the agent.
    """

    SECRET_KEY_FILE = ".agent_secrets.key"
    SECRETS_FILE = ".agent_secrets.enc"

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.key_path = self.project_dir / self.SECRET_KEY_FILE
        self.secrets_path = self.project_dir / self.SECRETS_FILE
        self._fernet: Optional[Fernet] = None

    def _get_fernet(self) -> Fernet:
        if self._fernet:
            return self._fernet

        key = self.load_key()
        if not key:
             raise ValueError("Encryption key not found. Run 'secrets init' first.")

        self._fernet = Fernet(key)
        return self._fernet

    def generate_key(self, force: bool = False) -> bool:
        """Generates a new encryption key."""
        if self.key_path.exists() and not force:
            return False

        key = Fernet.generate_key()
        # Set permission to 600 atomically
        fd = os.open(self.key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(key)
        # Ensure permissions are correct even if file existed with different permissions
        os.chmod(self.key_path, 0o600)
        return True

    def load_key(self) -> Optional[bytes]:
        """Loads the encryption key."""
        # Try env var first
        env_key = os.environ.get("AGENT_SECRET_KEY")
        if env_key:
            return env_key.encode()

        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                return f.read()
        return None

    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Encrypts and saves secrets to disk."""
        fernet = self._get_fernet()
        data = json.dumps(secrets).encode()
        encrypted = fernet.encrypt(data)

        fd = os.open(self.secrets_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(encrypted)
        # Ensure permissions are correct even if file existed with different permissions
        os.chmod(self.secrets_path, 0o600)

    def load_secrets(self) -> Dict[str, str]:
        """Loads and decrypts secrets from disk."""
        if not self.secrets_path.exists():
            return {}

        fernet = self._get_fernet()
        with open(self.secrets_path, "rb") as f:
            encrypted = f.read()

        try:
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted)
        except Exception:
             # If decryption fails, it usually means invalid key or corrupted file
             raise ValueError("Failed to decrypt secrets. Invalid key or corrupted file.")

    def set_secret(self, name: str, value: str) -> None:
        """Sets a secret."""
        secrets = self.load_secrets()
        secrets[name] = value
        self.save_secrets(secrets)

    def get_secret(self, name: str) -> Optional[str]:
        """Gets a decrypted secret."""
        secrets = self.load_secrets()
        return secrets.get(name)

    def list_secrets(self) -> List[str]:
        """Lists secret names."""
        secrets = self.load_secrets()
        return list(secrets.keys())

    def delete_secret(self, name: str) -> bool:
        """Deletes a secret."""
        secrets = self.load_secrets()
        if name in secrets:
            del secrets[name]
            self.save_secrets(secrets)
            return True
        return False

    def get_env_with_secrets(self) -> Dict[str, str]:
        """
        Returns a copy of the current environment variables with secrets injected.
        """
        secrets = self.load_secrets()
        env = os.environ.copy()
        env.update(secrets)
        return env
