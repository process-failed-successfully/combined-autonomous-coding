import unittest
import json
import base64
from unittest.mock import MagicMock
from shared.jwt_lab import JWTManager, run_jwt_lab_logic

class TestJWTManager(unittest.TestCase):
    def setUp(self):
        self.secret = "mysecret"
        self.payload = {"sub": "123", "name": "Test"}
        self.manager = JWTManager()

    def test_sign_token_structure(self):
        token = self.manager.sign_token(self.payload, self.secret)
        parts = token.split('.')
        self.assertEqual(len(parts), 3)

        # Verify header
        header_json = self.manager.base64url_decode(parts[0])
        header = json.loads(header_json)
        self.assertEqual(header['alg'], 'HS256')
        self.assertEqual(header['typ'], 'JWT')

    def test_verify_token_valid(self):
        token = self.manager.sign_token(self.payload, self.secret)
        decoded = self.manager.verify_token(token, self.secret)
        self.assertEqual(decoded['payload'], self.payload)

    def test_verify_token_invalid_signature(self):
        token = self.manager.sign_token(self.payload, self.secret)
        # Tamper with signature (last part)
        parts = token.split('.')
        parts[2] = "invalid_sig"
        tampered_token = '.'.join(parts)

        with self.assertRaisesRegex(ValueError, "Invalid signature"):
            self.manager.verify_token(tampered_token, self.secret)

    def test_verify_token_invalid_secret(self):
        token = self.manager.sign_token(self.payload, self.secret)
        with self.assertRaisesRegex(ValueError, "Invalid signature"):
            self.manager.verify_token(token, "wrong_secret")

    def test_decode_token(self):
        token = self.manager.sign_token(self.payload, self.secret)
        decoded = self.manager.decode_token(token)
        self.assertEqual(decoded['payload'], self.payload)
        self.assertEqual(decoded['header']['alg'], 'HS256')

    def test_run_logic_sign(self):
        args = MagicMock()
        args.action = "sign"
        args.payload = json.dumps(self.payload)
        args.secret = self.secret

        # We can't easily capture stdout here without patching,
        # but we can check if it returns True
        self.assertTrue(run_jwt_lab_logic(args))

    def test_run_logic_decode(self):
        token = self.manager.sign_token(self.payload, self.secret)
        args = MagicMock()
        args.action = "decode"
        args.token = token
        self.assertTrue(run_jwt_lab_logic(args))

    def test_run_logic_verify(self):
        token = self.manager.sign_token(self.payload, self.secret)
        args = MagicMock()
        args.action = "verify"
        args.token = token
        args.secret = self.secret
        args.verbose = False
        self.assertTrue(run_jwt_lab_logic(args))

if __name__ == '__main__':
    unittest.main()
