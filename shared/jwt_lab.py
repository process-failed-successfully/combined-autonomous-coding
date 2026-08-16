import base64
import json
import hmac
import hashlib
import time
import sys
import urllib.request
import urllib.error
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
    def fetch_jwks(jwks_url: str) -> dict:
        if not jwks_url.startswith("https://") and not jwks_url.startswith("http://"):
            raise ValueError("JWKS URL must use http or https scheme")

        try:
            req = urllib.request.Request(jwks_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
                else:
                    raise ValueError(f"Failed to fetch JWKS: HTTP {response.status}")
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to fetch JWKS from URL: {e}")
        except json.JSONDecodeError:
            raise ValueError("Failed to parse JWKS JSON response.")

    @staticmethod
    def get_public_key_from_jwks(jwks: dict, kid: str) -> str:
        keys = jwks.get("keys", [])
        for key in keys:
            if key.get("kid") == kid:
                if key.get("kty") == "RSA":
                    # Convert JWK RSA parts (n, e) to PEM format
                    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
                    from cryptography.hazmat.primitives import serialization

                    e_bytes = JWTManager.base64url_decode(key["e"])
                    n_bytes = JWTManager.base64url_decode(key["n"])

                    e = int.from_bytes(e_bytes, byteorder='big')
                    n = int.from_bytes(n_bytes, byteorder='big')

                    public_numbers = RSAPublicNumbers(e, n)
                    public_key = public_numbers.public_key()
                    pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    return pem.decode('utf-8')
                else:
                    raise ValueError(f"Unsupported JWK key type (kty): {key.get('kty')}")
        raise ValueError(f"Key with kid '{kid}' not found in JWKS.")

    @staticmethod
    def verify_token(token: str, secret: str = "", jwks_url: str = "") -> dict:
        decoded = JWTManager.decode_token(token)
        header = decoded["header"]

        algo = header.get("alg")
        if algo not in JWTManager.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm for verification: {algo}")

        if jwks_url and not secret:
            if algo.startswith("HS"):
                raise ValueError("Key confusion vulnerability detected: token specifies HMAC but JWKS requires asymmetric keys.")
            kid = header.get("kid")
            if not kid:
                raise ValueError("Token header missing 'kid', required for JWKS verification.")
            jwks = JWTManager.fetch_jwks(jwks_url)
            secret = JWTManager.get_public_key_from_jwks(jwks, kid)

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

    @staticmethod
    def crack_token(token: str, wordlist_path: str) -> str | None:
        """
        Attempts to crack the secret of an HMAC JWT token using a wordlist.
        """
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format (expected 3 parts)")

        header_b64, payload_b64, signature_b64 = parts

        try:
            header_json = JWTManager.base64url_decode(header_b64)
            header = json.loads(header_json)
        except Exception as e:
            raise ValueError(f"Failed to decode token header: {e}")

        algo = header.get("alg")
        if not algo or not algo.startswith("HS"):
            raise ValueError(f"Cracking is only supported for HMAC algorithms (HS256, HS384, HS512). Token uses: {algo}")

        if algo not in JWTManager.ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algo}")

        hash_func = JWTManager.ALGORITHMS[algo]
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    secret = line.strip()
                    if not secret:
                        continue

                    expected_signature = hmac.new(secret.encode('utf-8'), signing_input, hash_func).digest()
                    expected_signature_b64 = JWTManager.base64url_encode(expected_signature)

                    if hmac.compare_digest(signature_b64, expected_signature_b64):
                        return secret
        except FileNotFoundError:
            raise ValueError(f"Wordlist file not found: {wordlist_path}")

        return None


    @staticmethod
    def extract_field(token: str, field_path: str) -> str:
        """
        Extracts a specific field from the decoded token based on a dot-notated path.
        Example: 'payload.sub', 'header.alg'
        """
        decoded = JWTManager.decode_token(token)

        parts = field_path.split('.')
        current = decoded

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"Field '{field_path}' not found in token.")

        if isinstance(current, (dict, list)):
            import json
            return json.dumps(current)
        return str(current)

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
                secret = getattr(args, 'secret', None) or ""
                jwks_url = getattr(args, 'jwks_url', None) or ""

                if not secret and not jwks_url:
                    print("Error: Either --secret or --jwks-url is required.", file=sys.stderr)
                    return False

                result = manager.verify_token(args.token, secret=secret, jwks_url=jwks_url)
                print("✅ Signature Verified")
                if hasattr(args, 'verbose') and args.verbose:
                    print(json.dumps(result, indent=2))
                return True
            except ValueError as e:
                print(f"❌ Verification Failed: {e}", file=sys.stderr)
                return False

        elif args.action == "extract":
            try:
                result = manager.extract_field(args.token, args.field)
                print(result)
                return True
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return False

        elif args.action == "crack":
            print(f"Attempting to crack token using wordlist: {args.wordlist}...")
            start_time = time.time()
            try:
                secret = manager.crack_token(args.token, args.wordlist)
                elapsed = time.time() - start_time
                if secret:
                    print(f"✅ CRACKED! Secret found: {secret}")
                    print(f"Time taken: {elapsed:.2f}s")
                    return True
                else:
                    print(f"❌ Failed to crack token. Secret not in wordlist.")
                    print(f"Time taken: {elapsed:.2f}s")
                    return False
            except ValueError as e:
                print(f"❌ Error: {e}", file=sys.stderr)
                return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    return False
