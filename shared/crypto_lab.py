import hashlib
import uuid
import secrets
import base64
import sys
from pathlib import Path
from typing import Union, Optional
from cryptography.fernet import Fernet

class CryptoLabManager:
    """
    Manages cryptographic operations: hashing, encryption, decryption, and random generation.
    """

    def __init__(self):
        pass

    def hash_data(self, input_data: Union[str, bytes], algo: str = "sha256") -> str:
        """
        Calculates the hash digest of the input data.
        Supported algorithms: md5, sha1, sha256, sha512.
        """
        if isinstance(input_data, str):
            data_bytes = input_data.encode("utf-8")
        else:
            data_bytes = input_data

        algo = algo.lower()
        if algo not in hashlib.algorithms_available:
             # Fallback check for common ones guaranteed by hashlib
             if algo not in ["md5", "sha1", "sha256", "sha512"]:
                 raise ValueError(f"Unsupported algorithm: {algo}")

        hasher = hashlib.new(algo)
        hasher.update(data_bytes)
        return hasher.hexdigest()

    def generate_key(self) -> bytes:
        """Generates a Fernet key."""
        return Fernet.generate_key()

    def encrypt_data(self, input_data: Union[str, bytes], key: bytes) -> bytes:
        """
        Encrypts data using Fernet (symmetric encryption).
        """
        f = Fernet(key)
        if isinstance(input_data, str):
            data_bytes = input_data.encode("utf-8")
        else:
            data_bytes = input_data
        return f.encrypt(data_bytes)

    def decrypt_data(self, input_data: bytes, key: bytes) -> bytes:
        """
        Decrypts data using Fernet.
        """
        f = Fernet(key)
        return f.decrypt(input_data)

    def generate_random(self, length: int = 32, type: str = "hex") -> str:
        """
        Generates random data.
        Types: hex, base64, uuid, int.
        """
        if type == "hex":
            return secrets.token_hex(length // 2) # token_hex takes nbytes, returns 2*nbytes chars
        elif type == "base64":
            return secrets.token_urlsafe(length)
        elif type == "uuid":
            return str(uuid.uuid4())
        elif type == "int":
            # Just a random integer with 'length' bits? Or up to length?
            # Let's interpret length as number of bytes converted to int
            return str(int.from_bytes(secrets.token_bytes(length), byteorder="big"))
        else:
            raise ValueError(f"Unknown type: {type}")

def run_crypto_lab_logic(args) -> bool:
    """
    CLI logic for Crypto Lab.
    """
    manager = CryptoLabManager()

    try:
        if args.action == "hash":
            data = None
            if args.file:
                path = Path(args.file)
                if not path.exists():
                    print(f"Error: File {path} not found.", file=sys.stderr)
                    return False
                data = path.read_bytes()
            elif args.text:
                data = args.text
            else:
                # Read from stdin
                if not sys.stdin.isatty():
                    try:
                        data = sys.stdin.buffer.read()
                    except Exception:
                        data = sys.stdin.read().encode("utf-8")
                else:
                    print("Error: Input text or file required.", file=sys.stderr)
                    return False

            result = manager.hash_data(data, args.algo)
            print(result)
            return True

        elif args.action == "gen-key":
            key = manager.generate_key()
            if args.output:
                Path(args.output).write_bytes(key)
                print(f"Key saved to {args.output}")
            else:
                print(key.decode("utf-8"))
            return True

        elif args.action == "encrypt":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                path = Path(args.key_file)
                if not path.exists():
                    print(f"Error: Key file {path} not found.", file=sys.stderr)
                    return False
                key = path.read_bytes().strip()

            if not key:
                print("Error: Key required (--key or --key-file).", file=sys.stderr)
                return False

            data = None
            if args.input:
                data = args.input
            elif args.input_file:
                path = Path(args.input_file)
                if not path.exists():
                    print(f"Error: Input file {path} not found.", file=sys.stderr)
                    return False
                data = path.read_bytes()
            else:
                 # Read from stdin
                if not sys.stdin.isatty():
                    try:
                        data = sys.stdin.buffer.read()
                    except Exception:
                        data = sys.stdin.read().encode("utf-8")
                else:
                    print("Error: Input required.", file=sys.stderr)
                    return False

            encrypted = manager.encrypt_data(data, key)

            if args.output:
                Path(args.output).write_bytes(encrypted)
                print(f"Encrypted data saved to {args.output}")
            else:
                print(encrypted.decode("utf-8"))
            return True

        elif args.action == "decrypt":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                path = Path(args.key_file)
                if not path.exists():
                    print(f"Error: Key file {path} not found.", file=sys.stderr)
                    return False
                key = path.read_bytes().strip()

            if not key:
                print("Error: Key required (--key or --key-file).", file=sys.stderr)
                return False

            data = None
            if args.input:
                # If input is string, it might be the base64 encoded encrypted data
                data = args.input.encode("utf-8")
            elif args.input_file:
                path = Path(args.input_file)
                if not path.exists():
                    print(f"Error: Input file {path} not found.", file=sys.stderr)
                    return False
                data = path.read_bytes()
            else:
                 # Read from stdin
                if not sys.stdin.isatty():
                    data = sys.stdin.buffer.read().strip()
                else:
                    print("Error: Input required.", file=sys.stderr)
                    return False

            try:
                decrypted = manager.decrypt_data(data, key)
            except Exception as e:
                print(f"Error decrypting: {e}", file=sys.stderr)
                return False

            if args.output:
                Path(args.output).write_bytes(decrypted)
                print(f"Decrypted data saved to {args.output}")
            else:
                # Try to print as text, if fails, print repr
                try:
                    print(decrypted.decode("utf-8"))
                except UnicodeDecodeError:
                    print(decrypted) # Bytes repr
            return True

        elif args.action == "random":
            result = manager.generate_random(args.length, args.type)
            print(result)
            return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    return False
