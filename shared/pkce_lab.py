import argparse
import base64
import hashlib
import os
import re
from typing import Dict, Any, Optional

class PkceManager:
    """Manager for Proof Key for Code Exchange (PKCE) operations."""

    @staticmethod
    def generate_verifier(length: int = 43) -> str:
        """
        Generates a PKCE code verifier.
        The length must be between 43 and 128 characters.
        """
        if length < 43 or length > 128:
            raise ValueError("Code verifier length must be between 43 and 128 characters")

        # Generate random bytes
        num_bytes = int(length * 3 / 4) + 1  # Approximate number of bytes needed for base64 length
        rand_bytes = os.urandom(num_bytes)

        # Base64url encode and strip padding
        verifier = base64.urlsafe_b64encode(rand_bytes).decode('utf-8').rstrip('=')

        # Truncate to desired length and ensure it matches [a-zA-Z0-9-._~]
        verifier = verifier[:length]
        # Replace any non-allowed characters just in case (though urlsafe_b64encode handles +/ to -_)
        verifier = re.sub(r'[^a-zA-Z0-9\-._~]', 'A', verifier)

        return verifier

    @staticmethod
    def generate_challenge(verifier: str, method: str = "S256") -> str:
        """
        Generates a PKCE code challenge from a verifier.
        Supports 'S256' and 'plain' methods.
        """
        if method.upper() == "S256":
            hashed = hashlib.sha256(verifier.encode('ascii')).digest()
            challenge = base64.urlsafe_b64encode(hashed).decode('utf-8').rstrip('=')
            return challenge
        elif method.lower() == "plain":
            return verifier
        else:
            raise ValueError("Unsupported challenge method. Use 'S256' or 'plain'.")

    @staticmethod
    def verify(verifier: str, challenge: str, method: str = "S256") -> bool:
        """
        Verifies that a code verifier matches a given challenge.
        """
        expected_challenge = PkceManager.generate_challenge(verifier, method)
        return expected_challenge == challenge


def run_pkce_lab_logic(args: argparse.Namespace) -> None:
    """Handles CLI commands for PKCE Lab."""

    # Check if TUI is requested
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from main import run_tui
        run_tui(args)
        return

    action = getattr(args, "action", None)
    manager = PkceManager()

    if action == "generate":
        length = getattr(args, "length", 43)
        try:
            verifier = manager.generate_verifier(length=length)
            print(verifier)
        except ValueError as e:
            print(f"Error: {e}")
    elif action == "challenge":
        verifier = getattr(args, "verifier", None)
        method = getattr(args, "method", "S256")
        if not verifier:
            print("Error: --verifier is required for 'challenge' action.")
            return
        try:
            challenge = manager.generate_challenge(verifier, method)
            print(challenge)
        except ValueError as e:
            print(f"Error: {e}")
    elif action == "verify":
        verifier = getattr(args, "verifier", None)
        challenge = getattr(args, "challenge", None)
        method = getattr(args, "method", "S256")

        if not verifier or not challenge:
            print("Error: Both --verifier and --challenge are required for 'verify' action.")
            return

        is_valid = manager.verify(verifier, challenge, method)
        if is_valid:
            print("Valid: Challenge matches Verifier.")
        else:
            print("Invalid: Challenge DOES NOT match Verifier.")
    else:
        print("Invalid action. Use 'generate', 'challenge', 'verify', or 'tui'.")
