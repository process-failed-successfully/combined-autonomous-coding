import unittest
from shared.jwt_lab import JWTManager
import json
import base64

class TestJWTManager(unittest.TestCase):
    def setUp(self):
        self.manager = JWTManager()
        self.payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
        self.secret = "mysecret"

    def test_sign_and_verify_hs256(self):
        token = self.manager.sign_token(self.payload, self.secret, "HS256")
        self.assertIsInstance(token, str)
        decoded = self.manager.verify_token(token, self.secret)
        self.assertEqual(decoded["payload"], self.payload)
        self.assertEqual(decoded["header"]["alg"], "HS256")

    def test_sign_and_verify_hs384(self):
        token = self.manager.sign_token(self.payload, self.secret, "HS384")
        self.assertIsInstance(token, str)
        decoded = self.manager.verify_token(token, self.secret)
        self.assertEqual(decoded["payload"], self.payload)
        self.assertEqual(decoded["header"]["alg"], "HS384")

    def test_sign_and_verify_hs512(self):
        token = self.manager.sign_token(self.payload, self.secret, "HS512")
        self.assertIsInstance(token, str)
        decoded = self.manager.verify_token(token, self.secret)
        self.assertEqual(decoded["payload"], self.payload)
        self.assertEqual(decoded["header"]["alg"], "HS512")

    def test_decode_token(self):
        token = self.manager.sign_token(self.payload, self.secret, "HS256")
        decoded = self.manager.decode_token(token)
        self.assertEqual(decoded["payload"], self.payload)
        self.assertEqual(decoded["header"]["alg"], "HS256")
        self.assertIn("signature", decoded)

    def test_verify_invalid_signature(self):
        token = self.manager.sign_token(self.payload, self.secret, "HS256")
        with self.assertRaises(ValueError):
            self.manager.verify_token(token, "wrongsecret")

    def test_unsupported_algorithm(self):
        with self.assertRaises(ValueError):
            self.manager.sign_token(self.payload, self.secret, "UNKNOWNALG")

    def test_malformed_token(self):
        with self.assertRaises(ValueError):
            self.manager.decode_token("part1.part2")

    def test_invalid_base64(self):
        # Construct a token with invalid base64
        with self.assertRaises(ValueError):
            self.manager.decode_token("header.payload.signature")

    def test_sign_and_verify_rs256(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Sign with private key
        token = self.manager.sign_token(self.payload, private_pem, "RS256")
        self.assertIsInstance(token, str)

        # Verify with public key
        decoded_pub = self.manager.verify_token(token, public_pem)
        self.assertEqual(decoded_pub["payload"], self.payload)
        self.assertEqual(decoded_pub["header"]["alg"], "RS256")

        # Verify with private key (fallback functionality)
        decoded_priv = self.manager.verify_token(token, private_pem)
        self.assertEqual(decoded_priv["payload"], self.payload)

    def test_verify_rs256_invalid_signature(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem1 = private_key1.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        private_key2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem2 = private_key2.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Sign with key 1
        token = self.manager.sign_token(self.payload, private_pem1, "RS256")

        # Verify with key 2 (should fail)
        with self.assertRaises(ValueError) as context:
            self.manager.verify_token(token, public_pem2)
        self.assertEqual(str(context.exception), "Invalid signature")

    def test_key_confusion_vulnerability_prevention(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Attacker creates a forged token with HS256, but signs it using the public key as the symmetric secret
        forged_token = self.manager.sign_token(self.payload, public_pem, "HS256")

        # System attempts to verify the token, expecting an RSA token, but the token says HS256
        with self.assertRaises(ValueError) as context:
            self.manager.verify_token(forged_token, public_pem)

        self.assertEqual(str(context.exception), "Key confusion vulnerability detected: token specifies HMAC but an asymmetric key was provided.")

    def test_crack_token_success(self):
        # Create a temporary wordlist
        import tempfile
        import os

        token = self.manager.sign_token(self.payload, self.secret, "HS256")

        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write("wrongsecret1\n")
            f.write("wrongsecret2\n")
            f.write(self.secret + "\n")
            f.write("wrongsecret3\n")

        try:
            cracked_secret = self.manager.crack_token(token, path)
            self.assertEqual(cracked_secret, self.secret)
        finally:
            os.remove(path)

    def test_crack_token_failure(self):
        import tempfile
        import os

        token = self.manager.sign_token(self.payload, self.secret, "HS256")

        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write("wrongsecret1\n")
            f.write("wrongsecret2\n")

        try:
            cracked_secret = self.manager.crack_token(token, path)
            self.assertIsNone(cracked_secret)
        finally:
            os.remove(path)

    def test_verify_jwks_success(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from unittest.mock import patch
        import json

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_numbers = private_key.public_key().public_numbers()

        # Convert e and n to base64url format for JWKS
        e_bytes = public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder='big')
        n_bytes = public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder='big')

        e_b64 = JWTManager.base64url_encode(e_bytes)
        n_b64 = JWTManager.base64url_encode(n_bytes)

        kid = "test-key-id"

        jwks_data = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": kid,
                    "use": "sig",
                    "n": n_b64,
                    "e": e_b64
                }
            ]
        }

        # Sign token with custom kid in header
        algo = "RS256"
        header = {"typ": "JWT", "alg": algo, "kid": kid}
        header_b64 = JWTManager.base64url_encode(json.dumps(header).encode('utf-8'))
        payload_b64 = JWTManager.base64url_encode(json.dumps(self.payload).encode('utf-8'))

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = JWTManager.base64url_encode(signature)

        token = f"{header_b64}.{payload_b64}.{signature_b64}"

        with patch("shared.jwt_lab.urllib.request.urlopen") as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.status = 200
            mock_response.read.return_value = json.dumps(jwks_data).encode('utf-8')

            # Verify using JWKS
            decoded = self.manager.verify_token(token, jwks_url="https://example.com/.well-known/jwks.json")
            self.assertEqual(decoded["payload"], self.payload)

            # Test key not found
            bad_header = {"typ": "JWT", "alg": algo, "kid": "wrong-kid"}
            bad_header_b64 = JWTManager.base64url_encode(json.dumps(bad_header).encode('utf-8'))
            bad_token = f"{bad_header_b64}.{payload_b64}.{signature_b64}"
            with self.assertRaisesRegex(ValueError, "Key with kid 'wrong-kid' not found"):
                self.manager.verify_token(bad_token, jwks_url="https://example.com/.well-known/jwks.json")

            # Test vulnerability prevention: token specifies HS256 but requests JWKS validation
            vuln_header = {"typ": "JWT", "alg": "HS256", "kid": kid}
            vuln_header_b64 = JWTManager.base64url_encode(json.dumps(vuln_header).encode('utf-8'))
            vuln_token = f"{vuln_header_b64}.{payload_b64}.{signature_b64}"
            with self.assertRaisesRegex(ValueError, "token specifies HMAC but JWKS requires asymmetric keys"):
                self.manager.verify_token(vuln_token, jwks_url="https://example.com/.well-known/jwks.json")


    def test_crack_token_unsupported_algo(self):
        import tempfile
        import os
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        token = self.manager.sign_token(self.payload, private_pem, "RS256")

        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write("dummy\n")

        try:
            with self.assertRaises(ValueError) as context:
                self.manager.crack_token(token, path)
            self.assertIn("only supported for HMAC algorithms", str(context.exception))
        finally:
            os.remove(path)



    def test_extract_basic(self):
        token1 = self.manager.sign_token({"test": 1}, self.secret)
        token2 = self.manager.sign_token({"test": 2}, self.secret)
        text = f"Here is one token: {token1} and another one: {token2}."

        extracted = self.manager.extract(text)
        self.assertEqual(len(extracted), 2)
        self.assertIn(token1, extracted)
        self.assertIn(token2, extracted)

    def test_extract_unique(self):
        token1 = self.manager.sign_token({"test": 1}, self.secret)
        text = f"Token A: {token1} and again {token1}."

        extracted = self.manager.extract(text, unique=True)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], token1)

    def test_extract_invalid_skips(self):
        token1 = self.manager.sign_token({"test": 1}, self.secret)
        # Fake token with invalid base64 padding or signature
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid"
        text = f"Valid: {token1} Invalid: {invalid_token}"

        extracted = self.manager.extract(text)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0], token1)


import sys
from io import StringIO
from shared.jwt_lab import run_jwt_lab_logic, JWTManager

class TestJWTExtractCLI(unittest.TestCase):
    def test_extract_cli_action(self):
        manager = JWTManager()
        token = manager.sign_token({"foo": "bar"}, "secret")

        class Args:
            action = "extract"
            text = f"Token inside: {token}"
            unique = False

        args = Args()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        result = run_jwt_lab_logic(args)

        output = sys.stdout.getvalue().strip()
        sys.stdout = old_stdout

        self.assertTrue(result)
        self.assertEqual(output, token)

if __name__ == '__main__':
    unittest.main()
