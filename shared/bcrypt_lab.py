import argparse
import bcrypt
import sys

class BcryptLabManager:
    """Manages Bcrypt hashing and verification operations."""

    def hash_password(self, password: str, rounds: int = 12) -> str:
        """Hashes a password using bcrypt with the specified cost factor."""
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('ascii')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifies a password against a bcrypt hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('ascii'))


def run_bcrypt_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = BcryptLabManager()

        if getattr(args, "hash", None) is not None:
            password = args.hash
            rounds = getattr(args, "rounds", 12)
            try:
                hashed = manager.hash_password(password, rounds=rounds)
                print(hashed)
            except Exception as e:
                print(f"Error hashing password: {e}", file=sys.stderr)
                return False

        elif getattr(args, "verify", None) is not None:
            if not getattr(args, "hash_value", None):
                print("Error: must provide --hash-value to verify against", file=sys.stderr)
                return False

            password = args.verify
            hashed = args.hash_value

            try:
                is_valid = manager.verify_password(password, hashed)
                if is_valid:
                    print("Match: True")
                else:
                    print("Match: False")
                    return False
            except Exception as e:
                print(f"Error verifying password: {e}", file=sys.stderr)
                return False

        else:
            print("Error: must provide either --hash, --verify, or --tui", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error processing bcrypt: {e}", file=sys.stderr)
        return False
