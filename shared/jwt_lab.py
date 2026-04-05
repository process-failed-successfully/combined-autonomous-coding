import base64
import json
import hmac
import hashlib
import time
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature

class JWTManager:
    ALGORITHMS = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
        "RS256": hashes.SHA256,
        "RS384": hashes.SHA384,
        "RS512": hashes.SHA512
    }

    @staticmethod
    def base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

    @staticmethod
    def base64url_decode(data: str) -> bytes:
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)

    @staticmethod
    def sign_token(payload: dict, secret: str, algo: str = "HS256") -> str:
        if algo not in JWTManager.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algo}")

        header = {"typ": "JWT", "alg": algo}

        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        header_b64 = JWTManager.base64url_encode(header_json)
        payload_b64 = JWTManager.base64url_encode(payload_json)

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

        if algo.startswith("HS"):
            hash_func = JWTManager.ALGORITHMS[algo]
            signature = hmac.new(secret.encode('utf-8'), signing_input, hash_func).digest()
        elif algo.startswith("RS"):
            try:
                private_key = load_pem_private_key(secret.encode('utf-8'), password=None)
            except Exception as e:
                raise ValueError(f"Invalid RSA private key: {e}")

            hash_func = JWTManager.ALGORITHMS[algo]()
            signature = private_key.sign(
                signing_input,
                padding.PKCS1v15(),
                hash_func
            )
        else:
            raise ValueError(f"Unsupported algorithm type: {algo}")

        signature_b64 = JWTManager.base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @staticmethod
    def decode_token(token: str) -> dict:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format (expected 3 parts)")

        header_b64, payload_b64, signature_b64 = parts

        try:
            header_json = JWTManager.base64url_decode(header_b64)
            payload_json = JWTManager.base64url_decode(payload_b64)

            header = json.loads(header_json)
            payload = json.loads(payload_json)

            return {
                "header": header,
                "payload": payload,
                "signature": signature_b64
            }
        except Exception as e:
            raise ValueError(f"Failed to decode token: {e}")

    @staticmethod
    def verify_token(token: str, secret: str) -> dict:
        decoded = JWTManager.decode_token(token)
        header = decoded["header"]

        algo = header.get("alg")
        if algo not in JWTManager.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm for verification: {algo}")

        # Mitigate Algorithm Substitution (Key Confusion) vulnerability
        # If the token claims to use HMAC (HS*), but the secret provided is an asymmetric key (PEM format),
        # reject it to prevent attackers from using the public key as an HMAC secret.
        if algo.startswith("HS"):
            if "-----BEGIN " in secret:
                raise ValueError("Key confusion vulnerability detected: token specifies HMAC but an asymmetric key was provided.")

        parts = token.split('.')
        signing_input = f"{parts[0]}.{parts[1]}".encode('utf-8')
        signature_b64 = parts[2]
        signature = JWTManager.base64url_decode(signature_b64)

        if algo.startswith("HS"):
            hash_func = JWTManager.ALGORITHMS[algo]
            expected_signature = hmac.new(secret.encode('utf-8'), signing_input, hash_func).digest()
            expected_signature_b64 = JWTManager.base64url_encode(expected_signature)

            # Constant time comparison
            if not hmac.compare_digest(signature_b64, expected_signature_b64):
                raise ValueError("Invalid signature")
        elif algo.startswith("RS"):
            try:
                # Try loading as public key first
                public_key = load_pem_public_key(secret.encode('utf-8'))
            except Exception:
                try:
                    # Fallback to loading as private key and extracting public key
                    private_key = load_pem_private_key(secret.encode('utf-8'), password=None)
                    public_key = private_key.public_key()
                except Exception as e:
                    raise ValueError(f"Invalid RSA public/private key: {e}")

            hash_func = JWTManager.ALGORITHMS[algo]()
            try:
                public_key.verify(
                    signature,
                    signing_input,
                    padding.PKCS1v15(),
                    hash_func
                )
            except InvalidSignature:
                raise ValueError("Invalid signature")
        else:
            raise ValueError(f"Unsupported algorithm type: {algo}")

        # Check expiration
        payload = decoded["payload"]
        if "exp" in payload:
            try:
                exp = float(payload["exp"])
                if time.time() > exp:
                    raise ValueError("Token has expired")
            except (ValueError, TypeError):
                 pass # Ignore invalid exp type issues for now

        return decoded

def run_jwt_lab_logic(args) -> bool:
    manager = JWTManager()

    try:
        if args.action == "decode":
            result = manager.decode_token(args.token)
            print(json.dumps(result, indent=2))
            return True

        elif args.action == "sign":
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                print("Error: Payload must be valid JSON string.", file=sys.stderr)
                return False

            algo = getattr(args, 'algo', 'HS256')
            token = manager.sign_token(payload, args.secret, algo)
            print(token)
            return True

        elif args.action == "verify":
            try:
                result = manager.verify_token(args.token, args.secret)
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
