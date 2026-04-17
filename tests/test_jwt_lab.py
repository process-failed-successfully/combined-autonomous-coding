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


if __name__ == '__main__':
    unittest.main()
