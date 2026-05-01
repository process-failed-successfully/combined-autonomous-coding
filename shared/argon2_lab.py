import argparse
import sys
import getpass

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False

class Argon2LabManager:
    """Manages Argon2 password hashing and verification."""

    def __init__(self):
        if not HAS_ARGON2:
            raise ImportError(
                "argon2-cffi library not installed. "
                "Please install it using 'pip install argon2-cffi'."
            )

    def hash_password(
        self,
        password: str,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32
    ) -> str:
        """
        Hashes a password using Argon2id.
        """
        ph = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len
        )
        return ph.hash(password)

    def verify_password(self, password: str, hash_str: str) -> bool:
        """
        Verifies a password against an Argon2 hash.
        """
        ph = PasswordHasher()
        try:
            return ph.verify(hash_str, password)
        except VerifyMismatchError:
            return False

def run_argon2_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Argon2 Lab."""
    try:
        manager = Argon2LabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    if args.action == "hash":
        password = args.password
        if not password:
            if not sys.stdin.isatty():
                password = sys.stdin.read().strip()
            else:
                password = getpass.getpass("Enter password to hash: ")

        if not password:
            print("Error: Password is required.", file=sys.stderr)
            return False

        try:
            hashed = manager.hash_password(
                password=password,
                time_cost=args.time_cost,
                memory_cost=args.memory_cost,
                parallelism=args.parallelism,
                hash_len=args.hash_len
            )
            print(hashed)
            return True
        except Exception as e:
            print(f"Error hashing password: {e}", file=sys.stderr)
            return False

    elif args.action == "verify":
        password = args.password
        if not password:
            if not sys.stdin.isatty():
                password = sys.stdin.read().strip()
            else:
                password = getpass.getpass("Enter password to verify: ")

        if not password:
            print("Error: Password is required.", file=sys.stderr)
            return False

        try:
            is_valid = manager.verify_password(password, args.hash)
            if is_valid:
                print("✅ Password is valid.")
                return True
            else:
                print("❌ Invalid password.")
                return False
        except Exception as e:
            print(f"Error verifying password: {e}", file=sys.stderr)
            return False

    return False
