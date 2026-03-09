import hashlib
import uuid
import secrets
import base64
import sys
from pathlib import Path
from typing import Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

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
            return secrets.token_hex(length // 2)  # token_hex takes nbytes, returns 2*nbytes chars
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



    def generate_rsa_keypair(self) -> tuple[bytes, bytes]:
        """Generates an RSA private and public key pair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_bytes, public_bytes

    def rsa_encrypt(self, input_data: Union[str, bytes], public_key_bytes: bytes) -> bytes:
        """Encrypts data using an RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_bytes)
        if isinstance(input_data, str):
            data_bytes = input_data.encode("utf-8")
        else:
            data_bytes = input_data
        ciphertext = public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def rsa_decrypt(self, input_data: bytes, private_key_bytes: bytes) -> bytes:
        """Decrypts data using an RSA private key."""
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
        )
        plaintext = private_key.decrypt(
            input_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext

    def rsa_sign(self, input_data: Union[str, bytes], private_key_bytes: bytes) -> bytes:
        """Signs data using an RSA private key."""
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
        )
        if isinstance(input_data, str):
            data_bytes = input_data.encode("utf-8")
        else:
            data_bytes = input_data
        signature = private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def rsa_verify(self, input_data: Union[str, bytes], signature: bytes, public_key_bytes: bytes) -> bool:
        """Verifies a signature using an RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_bytes)
        if isinstance(input_data, str):
            data_bytes = input_data.encode("utf-8")
        else:
            data_bytes = input_data
        try:
            public_key.verify(
                signature,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False



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
                    print(decrypted)  # Bytes repr
            return True


        elif args.action == "rsa-keygen":
            priv, pub = manager.generate_rsa_keypair()
            if args.output:
                Path(f"{args.output}").write_bytes(priv)
                Path(f"{args.output}.pub").write_bytes(pub)
                print(f"Keypair saved to {args.output} and {args.output}.pub")
            else:
                print("--- Private Key ---")
                print(priv.decode('utf-8'))
                print("--- Public Key ---")
                print(pub.decode('utf-8'))
            return True

        elif args.action == "rsa-encrypt":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                key = Path(args.key_file).read_bytes()
            if not key:
                print("Error: Public key required.", file=sys.stderr)
                return False

            data = args.text if args.text else Path(args.file).read_bytes() if args.file else sys.stdin.buffer.read()
            encrypted = manager.rsa_encrypt(data, key)
            if args.output:
                Path(args.output).write_bytes(encrypted)
            else:
                print(base64.b64encode(encrypted).decode('utf-8'))
            return True

        elif args.action == "rsa-decrypt":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                key = Path(args.key_file).read_bytes()
            if not key:
                print("Error: Private key required.", file=sys.stderr)
                return False

            if args.input:
                data = base64.b64decode(args.input)
            elif args.input_file:
                data = Path(args.input_file).read_bytes()
            else:
                data = sys.stdin.buffer.read()

            decrypted = manager.rsa_decrypt(data, key)
            if args.output:
                Path(args.output).write_bytes(decrypted)
            else:
                print(decrypted.decode('utf-8', errors='replace'))
            return True

        elif args.action == "rsa-sign":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                key = Path(args.key_file).read_bytes()
            if not key:
                print("Error: Private key required.", file=sys.stderr)
                return False

            data = args.text if args.text else Path(args.file).read_bytes() if args.file else sys.stdin.buffer.read()
            signature = manager.rsa_sign(data, key)
            if args.output:
                Path(args.output).write_bytes(signature)
            else:
                print(base64.b64encode(signature).decode('utf-8'))
            return True

        elif args.action == "rsa-verify":
            key = None
            if args.key:
                key = args.key.encode("utf-8")
            elif args.key_file:
                key = Path(args.key_file).read_bytes()
            if not key:
                print("Error: Public key required.", file=sys.stderr)
                return False

            data = args.text if args.text else Path(args.file).read_bytes() if args.file else sys.stdin.buffer.read()

            if args.signature:
                signature = base64.b64decode(args.signature)
            elif args.signature_file:
                signature = Path(args.signature_file).read_bytes()
            else:
                print("Error: Signature required.", file=sys.stderr)
                return False

            if manager.rsa_verify(data, signature, key):
                print("Signature Verified: OK")
                return True
            else:
                print("Signature Verified: FAILED", file=sys.stderr)
                return False

        elif args.action == "random":
            result = manager.generate_random(args.length, args.type)
            print(result)
            return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    return False
