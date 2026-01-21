"""
Secrets Manager
===============

Handles secure encryption, decryption, and rotation of secrets.
Uses PBKDF2 for key derivation and Fernet (AES) for encryption.
"""

import os
import base64
import getpass
import secrets
import shutil
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich.console import Console

console = Console()

class SecretsManager:
    """
    Manages secure encryption and decryption of files (e.g., .env)
    and secret rotation.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derives a URL-safe base64-encoded key from a password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_file(self, input_path: Path, output_path: Optional[Path] = None, password: Optional[str] = None) -> bool:
        """
        Encrypts a file using a password.
        The salt is generated randomly and prepended to the output file.
        """
        if not input_path.exists():
            console.print(f"[red]Error: Input file {input_path} not found.[/red]")
            return False

        if not password:
            password = getpass.getpass("Enter encryption password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                console.print("[red]Error: Passwords do not match.[/red]")
                return False

        if not output_path:
            output_path = input_path.with_suffix(input_path.suffix + ".enc")

        try:
            # Generate a random 16-byte salt
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            f = Fernet(key)

            with open(input_path, "rb") as file:
                file_data = file.read()

            encrypted_data = f.encrypt(file_data)

            with open(output_path, "wb") as file:
                # Store salt first, then encrypted data
                file.write(salt)
                file.write(encrypted_data)

            console.print(f"[green]✅ Encrypted {input_path.name} to {output_path.name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error during encryption: {e}[/red]")
            return False

    def decrypt_file(self, input_path: Path, output_path: Optional[Path] = None, password: Optional[str] = None) -> bool:
        """
        Decrypts a file using a password.
        Reads the salt from the beginning of the file.
        """
        if not input_path.exists():
            console.print(f"[red]Error: Input file {input_path} not found.[/red]")
            return False

        if not password:
            password = getpass.getpass("Enter decryption password: ")

        if not output_path:
            # Try to remove .enc suffix if present
            if input_path.suffix == ".enc":
                output_path = input_path.with_suffix("")
            else:
                output_path = input_path.with_suffix(input_path.suffix + ".dec")

        try:
            with open(input_path, "rb") as file:
                # Read salt (first 16 bytes)
                salt = file.read(16)
                encrypted_data = file.read()

            key = self._derive_key(password, salt)
            f = Fernet(key)

            decrypted_data = f.decrypt(encrypted_data)

            with open(output_path, "wb") as file:
                file.write(decrypted_data)

            console.print(f"[green]✅ Decrypted {input_path.name} to {output_path.name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Error during decryption: {e}[/red]")
            console.print("[yellow]Verify your password and ensure the file is valid.[/yellow]")
            return False

    def rotate_secret(self, file_path: Path, key: str, length: int = 32) -> bool:
        """
        Rotates a secret in a file (e.g., .env) by generating a new value.
        """
        if not file_path.exists():
            console.print(f"[red]Error: File {file_path} not found.[/red]")
            return False

        new_secret = secrets.token_urlsafe(length)

        try:
            lines = file_path.read_text().splitlines()
            new_lines = []
            updated = False

            for line in lines:
                if line.strip().startswith(f"{key}="):
                    new_lines.append(f"{key}={new_secret}")
                    updated = True
                else:
                    new_lines.append(line)

            if not updated:
                # If key doesn't exist, should we add it?
                # For rotation, usually implies it exists. Let's add it if missing.
                new_lines.append(f"{key}={new_secret}")
                console.print(f"[yellow]Key '{key}' not found, added new.[/yellow]")

            file_path.write_text("\n".join(new_lines) + "\n")
            console.print(f"[green]✅ Rotated secret for '{key}' in {file_path.name}[/green]")
            console.print(f"New Value: {new_secret}")
            return True

        except Exception as e:
            console.print(f"[red]Error rotating secret: {e}[/red]")
            return False

    def audit_secrets(self) -> None:
        """
        Uses SecurityAuditor to scan for plaintext secrets.
        This is a wrapper for convenience within the secrets CLI.
        """
        from shared.security import SecurityAuditor

        auditor = SecurityAuditor(self.project_dir)
        console.print("[bold]Scanning for exposed secrets...[/bold]")
        findings = auditor.scan_secrets()

        if not findings:
            console.print("[green]✅ No exposed secrets found in tracked files.[/green]")
        else:
            console.print(f"[red]⚠️  Found {len(findings)} potential secret(s):[/red]")
            for f in findings:
                console.print(f"  - {f['description']} in {f['file']}:{f['line']}")
                console.print(f"    Snippet: [italic]{f['snippet']}[/italic]")
