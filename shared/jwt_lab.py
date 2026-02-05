import base64
import json
import hmac
import hashlib
import time
import sys

class JWTManager:
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
        header = {"typ": "JWT", "alg": algo}

        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        header_b64 = JWTManager.base64url_encode(header_json)
        payload_b64 = JWTManager.base64url_encode(payload_json)

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

        if algo == "HS256":
            signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
        else:
            raise ValueError(f"Unsupported algorithm: {algo}")

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
        if algo != "HS256":
            raise ValueError(f"Unsupported algorithm for verification: {algo}")

        parts = token.split('.')
        signing_input = f"{parts[0]}.{parts[1]}".encode('utf-8')
        signature_b64 = parts[2]

        expected_signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_signature_b64 = JWTManager.base64url_encode(expected_signature)

        # Constant time comparison
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            raise ValueError("Invalid signature")

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

            token = manager.sign_token(payload, args.secret)
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
