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
            self.manager.sign_token(self.payload, self.secret, "RS256")

    def test_malformed_token(self):
        with self.assertRaises(ValueError):
            self.manager.decode_token("part1.part2")

    def test_invalid_base64(self):
        # Construct a token with invalid base64
        with self.assertRaises(ValueError):
            self.manager.decode_token("header.payload.signature")

if __name__ == '__main__':
    unittest.main()
