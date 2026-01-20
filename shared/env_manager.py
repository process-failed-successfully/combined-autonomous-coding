"""
Environment Variable Manager
============================

Manage .env files and synchronization with .env.example.
"""

import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class EnvManager:
    """Manages environment variables for the project."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.env_path = self.project_dir / ".env"
        self.example_path = self.project_dir / ".env.example"

    def init(self) -> Tuple[bool, str]:
        """
        Initializes .env and .env.example if they don't exist.
        Also adds .env to .gitignore.
        """
        created = []
        if not self.example_path.exists():
            self.example_path.touch()
            created.append(".env.example")

        if not self.env_path.exists():
            self.env_path.touch()
            created.append(".env")

        # Add to .gitignore
        gitignore_path = self.project_dir / ".gitignore"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if ".env" not in content.splitlines():
                with open(gitignore_path, "a") as f:
                    if not content.endswith("\n") and content:
                        f.write("\n")
                    f.write(".env\n")
                created.append("added .env to .gitignore")

        if created:
            return True, f"Initialized: {', '.join(created)}"
        return False, "Already initialized."

    def _parse_env(self, path: Path) -> Dict[str, Optional[str]]:
        """Parses a .env file into a dictionary."""
        if not path.exists():
            return {}

        env_vars = {}
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("=", 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else None
                env_vars[key] = value
        return env_vars

    def check(self) -> Tuple[bool, List[str], List[str]]:
        """
        Checks if .env keys match .env.example keys.
        Returns (is_valid, missing_in_env, missing_in_example)
        """
        if not self.example_path.exists():
            return False, [], ["No .env.example found"]

        env_vars = self._parse_env(self.env_path)
        example_vars = self._parse_env(self.example_path)

        missing_in_env = [k for k in example_vars.keys() if k not in env_vars]
        missing_in_example = [k for k in env_vars.keys() if k not in example_vars]

        return (len(missing_in_env) == 0 and len(missing_in_example) == 0), missing_in_env, missing_in_example

    def sync(self, interactive: bool = False) -> Tuple[bool, str]:
        """
        Syncs keys between .env and .env.example.
        """
        if not self.example_path.exists():
             return False, ".env.example does not exist."

        env_vars = self._parse_env(self.env_path)
        example_vars = self._parse_env(self.example_path)

        missing_in_env = [k for k in example_vars.keys() if k not in env_vars]
        missing_in_example = [k for k in env_vars.keys() if k not in example_vars]

        if not missing_in_env and not missing_in_example:
            return True, "Files are already in sync."

        changes = []

        # Add missing keys to .env
        if missing_in_env:
            # Check for trailing newline before appending
            has_newline = True
            if self.env_path.exists() and self.env_path.stat().st_size > 0:
                with open(self.env_path, 'rb') as f:
                    f.seek(-1, 2)
                    has_newline = (f.read(1) == b'\n')

            with open(self.env_path, "a") as f:
                if not has_newline:
                    f.write("\n")

                for key in missing_in_env:
                    val = ""
                    if interactive:
                        val = input(f"Enter value for new key '{key}' (or leave empty): ").strip()
                    f.write(f"{key}={val}\n")
                    changes.append(f"Added {key} to .env")

        # Add missing keys to .env.example
        if missing_in_example:
            # Check for trailing newline before appending
            has_newline = True
            if self.example_path.exists() and self.example_path.stat().st_size > 0:
                with open(self.example_path, 'rb') as f:
                    f.seek(-1, 2)
                    has_newline = (f.read(1) == b'\n')

            with open(self.example_path, "a") as f:
                if not has_newline:
                    f.write("\n")

                for key in missing_in_example:
                    # Don't put actual secrets in example
                    f.write(f"{key}=\n")
                    changes.append(f"Added {key} to .env.example")

        return True, f"Synced: {', '.join(changes)}"

    def generate_secret(self, key: str, length: int = 32) -> str:
        """Generates a secure secret and updates/adds it to .env."""
        # Use a url-safe base64 string
        secret = secrets.token_urlsafe(length)

        # Read existing lines
        lines = []
        if self.env_path.exists():
            with open(self.env_path, "r") as f:
                lines = f.readlines()

        key_found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={secret}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={secret}\n")

        with open(self.env_path, "w") as f:
            f.writelines(new_lines)

        return secret
