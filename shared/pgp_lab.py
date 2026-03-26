import gnupg
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class PGPLabManager:
    """Manages PGP/GPG operations."""

    def __init__(self, gnupghome: Optional[str] = None):
        if not gnupghome:
            gnupghome = str(Path.home() / '.gnupg')
        Path(gnupghome).mkdir(mode=0o700, parents=True, exist_ok=True)
        self.gpg = gnupg.GPG(gnupghome=gnupghome)

    def generate_key(self, name_real: str, name_email: str, passphrase: str, key_type: str = "RSA", key_length: int = 2048) -> Optional[str]:
        input_data = self.gpg.gen_key_input(
            name_real=name_real,
            name_email=name_email,
            passphrase=passphrase,
            key_type=key_type,
            key_length=key_length
        )
        key = self.gpg.gen_key(input_data)
        if not key.fingerprint:
            return None
        return key.fingerprint

    def encrypt(self, data: str, recipients: List[str]) -> Optional[str]:
        encrypted_data = self.gpg.encrypt(data, recipients, always_trust=True)
        if not encrypted_data.ok:
            return None
        return str(encrypted_data)

    def decrypt(self, encrypted_data: str, passphrase: str) -> Optional[str]:
        decrypted_data = self.gpg.decrypt(encrypted_data, passphrase=passphrase)
        if not decrypted_data.ok:
            return None
        return str(decrypted_data)

    def sign(self, data: str, keyid: str, passphrase: str) -> Optional[str]:
        signed_data = self.gpg.sign(data, keyid=keyid, passphrase=passphrase)
        if not signed_data.fingerprint:
            return None
        return str(signed_data)

    def verify(self, signed_data: str) -> Optional[str]:
        verified = self.gpg.verify(signed_data)
        if not verified.valid:
            return None
        return str(verified.pubkey_fingerprint)

    def list_keys(self) -> List[Dict[str, Any]]:
        return self.gpg.list_keys()


def run_pgp_lab_logic(args: Any) -> bool:
    """CLI logic for PGP Lab."""
    manager = PGPLabManager()

    try:
        if args.action == "list":
            keys = manager.list_keys()
            for key in keys:
                print(f"Fingerprint: {key['fingerprint']}, UID: {key['uids']}")
            return True

        elif args.action == "generate":
            fingerprint = manager.generate_key(args.name, args.email, args.passphrase)
            if fingerprint:
                print(f"✅ Key generated successfully. Fingerprint: {fingerprint}")
                return True
            else:
                print("❌ Failed to generate key.", file=sys.stderr)
                return False

        elif args.action == "encrypt":
            if args.file:
                try:
                    with open(args.file, 'r') as f:
                        data = f.read()
                except Exception as e:
                    print(f"❌ Error reading file: {e}", file=sys.stderr)
                    return False
            elif args.text:
                data = args.text
            else:
                print("❌ Error: --text or --file must be provided.", file=sys.stderr)
                return False

            recipients = args.recipients.split(',')
            encrypted = manager.encrypt(data, recipients)
            if encrypted:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(encrypted)
                    print(f"✅ Encrypted data written to {args.output}")
                else:
                    print("✅ Encrypted Data:\n")
                    print(encrypted)
                return True
            else:
                print("❌ Encryption failed.", file=sys.stderr)
                return False

        elif args.action == "decrypt":
            if args.file:
                try:
                    with open(args.file, 'r') as f:
                        data = f.read()
                except Exception as e:
                    print(f"❌ Error reading file: {e}", file=sys.stderr)
                    return False
            elif args.text:
                data = args.text
            else:
                print("❌ Error: --text or --file must be provided.", file=sys.stderr)
                return False

            decrypted = manager.decrypt(data, args.passphrase)
            if decrypted:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(decrypted)
                    print(f"✅ Decrypted data written to {args.output}")
                else:
                    print("✅ Decrypted Data:\n")
                    print(decrypted)
                return True
            else:
                print("❌ Decryption failed.", file=sys.stderr)
                return False

        elif args.action == "sign":
            if args.file:
                try:
                    with open(args.file, 'r') as f:
                        data = f.read()
                except Exception as e:
                    print(f"❌ Error reading file: {e}", file=sys.stderr)
                    return False
            elif args.text:
                data = args.text
            else:
                print("❌ Error: --text or --file must be provided.", file=sys.stderr)
                return False

            signed = manager.sign(data, args.keyid, args.passphrase)
            if signed:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(signed)
                    print(f"✅ Signed data written to {args.output}")
                else:
                    print("✅ Signed Data:\n")
                    print(signed)
                return True
            else:
                print("❌ Signing failed.", file=sys.stderr)
                return False

        elif args.action == "verify":
            if args.file:
                try:
                    with open(args.file, 'r') as f:
                        data = f.read()
                except Exception as e:
                    print(f"❌ Error reading file: {e}", file=sys.stderr)
                    return False
            elif args.text:
                data = args.text
            else:
                print("❌ Error: --text or --file must be provided.", file=sys.stderr)
                return False

            fingerprint = manager.verify(data)
            if fingerprint:
                print(f"✅ Verification successful. Signature from key: {fingerprint}")
                return True
            else:
                print("❌ Verification failed.", file=sys.stderr)
                return False

    except Exception as e:
        print(f"❌ PGP operation failed: {e}", file=sys.stderr)
        return False

    return False
