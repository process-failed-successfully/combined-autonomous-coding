import sys
import json
from pyseto import Key, Paseto, PysetoError

class PasetoManager:
    """Manager for PASETO token operations using the pyseto library."""

    @staticmethod
    def create_key(version: int, purpose: str, key_material: bytes) -> Key:
        """Creates a pyseto Key object."""
        try:
            return Key.new(version=version, purpose=purpose, key=key_material)
        except Exception as e:
            raise ValueError(f"Failed to create PASETO key: {e}")

    @staticmethod
    def encode_token(payload: dict, key: Key, footer: dict = None, implicit_assertion: bytes = b"") -> str:
        """Encodes/signs a PASETO token."""
        try:
            p = Paseto.new()
            # Pyseto expects bytes for payload in some versions or dict
            payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            footer_bytes = json.dumps(footer, separators=(',', ':')).encode('utf-8') if footer else b""
            token = p.encode(
                key=key,
                payload=payload_bytes,
                footer=footer_bytes,
                implicit_assertion=implicit_assertion
            )
            if isinstance(token, bytes):
                return token.decode('utf-8')
            return token
        except PysetoError as e:
            raise ValueError(f"Failed to encode PASETO token: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error encoding PASETO token: {e}")

    @staticmethod
    def decode_token(token: str, key: Key = None, implicit_assertion: bytes = b"") -> dict:
        """Decodes/verifies a PASETO token."""
        try:
            if key is None:
                parts = token.split('.')
                if len(parts) < 3 or len(parts) > 4:
                    raise ValueError("Invalid PASETO token format.")

                return {
                    "version": parts[0],
                    "purpose": parts[1],
                    "payload": parts[2],
                    "footer": parts[3] if len(parts) == 4 else None
                }

            p = Paseto.new()
            decoded = p.decode(
                keys=[key],
                token=token,
                implicit_assertion=implicit_assertion
            )
            return {
                "version": decoded.version,
                "purpose": decoded.purpose,
                "payload": json.loads(decoded.payload.decode('utf-8')) if isinstance(decoded.payload, bytes) else decoded.payload,
                "footer": json.loads(decoded.footer.decode('utf-8')) if decoded.footer else None
            }
        except PysetoError as e:
            raise ValueError(f"Failed to decode/verify PASETO token: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error decoding PASETO token: {e}")

def run_paseto_lab_logic(args) -> bool:
    """CLI logic for PASETO Lab."""
    manager = PasetoManager()

    try:
        if args.action == "decode":
            if hasattr(args, 'key') and args.key:
                version = getattr(args, 'version', 4)
                purpose = getattr(args, 'purpose', 'local')
                key_material = args.key.encode('utf-8')
                try:
                     key = manager.create_key(version, purpose, key_material)
                except ValueError as e:
                     print(f"❌ {e}", file=sys.stderr)
                     return False

                implicit_assertion = getattr(args, 'implicit', b"")
                if isinstance(implicit_assertion, str):
                    implicit_assertion = implicit_assertion.encode('utf-8')

                result = manager.decode_token(args.token, key=key, implicit_assertion=implicit_assertion)
                print("✅ Token Verified & Decoded:")
                print(json.dumps(result, indent=2))
                return True
            else:
                result = manager.decode_token(args.token)
                print("⚠️ Token Unverified (Basic structure):")
                print(json.dumps(result, indent=2))
                return True

        elif args.action == "sign":
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                print("Error: Payload must be valid JSON string.", file=sys.stderr)
                return False

            footer = None
            if hasattr(args, 'footer') and args.footer:
                try:
                    footer = json.loads(args.footer)
                except json.JSONDecodeError:
                    print("Error: Footer must be valid JSON string.", file=sys.stderr)
                    return False

            version = getattr(args, 'version', 4)
            purpose = getattr(args, 'purpose', 'local')
            key_material = args.key.encode('utf-8')

            implicit_assertion = getattr(args, 'implicit', b"")
            if isinstance(implicit_assertion, str):
                implicit_assertion = implicit_assertion.encode('utf-8')

            try:
                key = manager.create_key(version, purpose, key_material)
            except ValueError as e:
                print(f"❌ {e}", file=sys.stderr)
                return False

            token = manager.encode_token(payload, key, footer=footer, implicit_assertion=implicit_assertion)
            print(token)
            return True

        elif args.action == "verify":
            if not hasattr(args, 'key') or not args.key:
                print("Error: --key argument is required for verification.", file=sys.stderr)
                return False

            version = getattr(args, 'version', 4)
            purpose = getattr(args, 'purpose', 'local')
            key_material = args.key.encode('utf-8')

            implicit_assertion = getattr(args, 'implicit', b"")
            if isinstance(implicit_assertion, str):
                implicit_assertion = implicit_assertion.encode('utf-8')

            try:
                key = manager.create_key(version, purpose, key_material)
                result = manager.decode_token(args.token, key=key, implicit_assertion=implicit_assertion)
                print("✅ Signature Verified")
                if hasattr(args, 'verbose') and args.verbose:
                    print(json.dumps(result, indent=2))
                return True
            except ValueError as e:
                print(f"❌ Verification Failed: {e}", file=sys.stderr)
                return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    return False
