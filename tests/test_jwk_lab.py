import unittest
from unittest.mock import patch
import io
import json
import argparse
from shared.jwk_lab import JwkManager, run_jwk_lab_logic
from cryptography.hazmat.primitives import serialization


class TestJwkLab(unittest.TestCase):
    def setUp(self):
        self.manager = JwkManager()

    def test_int_base64url_conversion(self):
        val = 123456789
        b64 = self.manager._int_to_base64url(val)
        val_back = self.manager._base64url_to_int(b64)
        self.assertEqual(val, val_back)

    def test_generate_rsa_key_and_jwk(self):
        key = self.manager.generate_rsa_key(1024)
        jwk = self.manager._rsa_to_jwk(key)
        self.assertEqual(jwk["kty"], "RSA")
        self.assertIn("n", jwk)
        self.assertIn("e", jwk)
        self.assertIn("d", jwk)
        self.assertIn("p", jwk)

        # test public key only
        pub_key = key.public_key()
        pub_jwk = self.manager._rsa_to_jwk(pub_key)
        self.assertEqual(pub_jwk["kty"], "RSA")
        self.assertIn("n", pub_jwk)
        self.assertNotIn("d", pub_jwk)

    def test_generate_ec_key_and_jwk(self):
        key = self.manager.generate_ec_key("P-256")
        jwk = self.manager._ec_to_jwk(key)
        self.assertEqual(jwk["kty"], "EC")
        self.assertEqual(jwk["crv"], "P-256")
        self.assertIn("x", jwk)
        self.assertIn("y", jwk)
        self.assertIn("d", jwk)

        # test public key only
        pub_key = key.public_key()
        pub_jwk = self.manager._ec_to_jwk(pub_key)
        self.assertEqual(pub_jwk["kty"], "EC")
        self.assertEqual(pub_jwk["crv"], "P-256")
        self.assertNotIn("d", pub_jwk)

    def test_invalid_ec_curve(self):
        with self.assertRaises(ValueError):
            self.manager.generate_ec_key("InvalidCurve")

    def test_unsupported_ec_curve_to_jwk(self):
        key = self.manager.generate_ec_key("P-256")
        with patch.object(key.curve, 'name', 'unsupported'):
            with self.assertRaises(ValueError):
                self.manager._ec_to_jwk(key)

    def test_pem_to_jwk_rsa(self):
        key = self.manager.generate_rsa_key(1024)
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        jwk = self.manager.pem_to_jwk(pem)
        self.assertEqual(jwk["kty"], "RSA")
        self.assertIn("d", jwk)

        # Test Public PEM
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        pub_jwk = self.manager.pem_to_jwk(pub_pem)
        self.assertEqual(pub_jwk["kty"], "RSA")
        self.assertNotIn("d", pub_jwk)

    def test_pem_to_jwk_ec(self):
        key = self.manager.generate_ec_key("P-256")
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        jwk = self.manager.pem_to_jwk(pem)
        self.assertEqual(jwk["kty"], "EC")
        self.assertEqual(jwk["crv"], "P-256")

        # Test Public PEM
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        pub_jwk = self.manager.pem_to_jwk(pub_pem)
        self.assertEqual(pub_jwk["kty"], "EC")
        self.assertNotIn("d", pub_jwk)

    def test_pem_to_jwk_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.pem_to_jwk("invalid pem string")

    @patch('shared.jwk_lab.serialization.load_pem_public_key')
    def test_pem_to_jwk_unsupported_type(self, mock_load):
        mock_load.return_value = "Not A Key"
        # Mock load_pem_private_key to raise ValueError so it falls back to public key
        with patch('shared.jwk_lab.serialization.load_pem_private_key', side_effect=ValueError):
            with self.assertRaises(ValueError):
                self.manager.pem_to_jwk("fake pem")

    def test_jwk_to_pem_rsa(self):
        key = self.manager.generate_rsa_key(1024)
        jwk = self.manager._rsa_to_jwk(key)

        pem = self.manager.jwk_to_pem(jwk)
        self.assertIn("BEGIN PRIVATE KEY", pem)

        # test public jwk
        pub_jwk = self.manager._rsa_to_jwk(key.public_key())
        pub_pem = self.manager.jwk_to_pem(pub_jwk)
        self.assertIn("BEGIN PUBLIC KEY", pub_pem)

    def test_jwk_to_pem_ec(self):
        key = self.manager.generate_ec_key("P-256")
        jwk = self.manager._ec_to_jwk(key)

        pem = self.manager.jwk_to_pem(jwk)
        self.assertIn("BEGIN PRIVATE KEY", pem)

        # test public
        pub_jwk = self.manager._ec_to_jwk(key.public_key())
        pub_pem = self.manager.jwk_to_pem(pub_jwk)
        self.assertIn("BEGIN PUBLIC KEY", pub_pem)

    def test_jwk_to_pem_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.jwk_to_pem({})  # Missing kty

        with self.assertRaises(ValueError):
            self.manager.jwk_to_pem({"kty": "UNKNOWN"})

        with self.assertRaises(ValueError):
            self.manager.jwk_to_pem({"kty": "EC", "crv": "UNKNOWN"})

        # missing primes RSA
        with self.assertRaises(ValueError):
            self.manager.jwk_to_pem({"kty": "RSA", "n": "AQAB", "e": "AQAB", "d": "AQAB"})

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_generate_rsa(self, mock_stdout):
        args = argparse.Namespace(action="generate", type="RSA", size=1024, kid="my-kid")
        res = run_jwk_lab_logic(args)
        self.assertTrue(res)
        out = mock_stdout.getvalue()
        parsed = json.loads(out)
        self.assertEqual(parsed["kty"], "RSA")
        self.assertEqual(parsed["kid"], "my-kid")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_generate_ec(self, mock_stdout):
        args = argparse.Namespace(action="generate", type="EC", curve="P-256", kid=None)
        res = run_jwk_lab_logic(args)
        self.assertTrue(res)
        out = mock_stdout.getvalue()
        parsed = json.loads(out)
        self.assertEqual(parsed["kty"], "EC")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_generate_invalid(self, mock_stderr):
        args = argparse.Namespace(action="generate", type="UNKNOWN")
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("Unsupported key type", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_pem2jwk(self, mock_stdout):
        key = self.manager.generate_rsa_key(1024)
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        args = argparse.Namespace(action="pem2jwk", pem=pem, password=None, kid="test")
        res = run_jwk_lab_logic(args)
        self.assertTrue(res)
        parsed = json.loads(mock_stdout.getvalue())
        self.assertEqual(parsed["kty"], "RSA")
        self.assertEqual(parsed["kid"], "test")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_pem2jwk_missing(self, mock_stderr):
        args = argparse.Namespace(action="pem2jwk", pem=None)
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("pem argument is required", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_jwk2pem(self, mock_stdout):
        key = self.manager.generate_rsa_key(1024)
        jwk = self.manager._rsa_to_jwk(key)

        args = argparse.Namespace(action="jwk2pem", jwk=json.dumps(jwk), password=None)
        res = run_jwk_lab_logic(args)
        self.assertTrue(res)
        self.assertIn("BEGIN PRIVATE KEY", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_jwk2pem_missing(self, mock_stderr):
        args = argparse.Namespace(action="jwk2pem", jwk=None)
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("jwk argument is required", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_jwk2pem_invalid_json(self, mock_stderr):
        args = argparse.Namespace(action="jwk2pem", jwk="not json")
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("Error parsing JWK JSON", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_unknown_action(self, mock_stderr):
        args = argparse.Namespace(action="unknown")
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("Unknown action", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_exception(self, mock_stderr):
        # Pass a bad curve to generate to trigger an exception
        args = argparse.Namespace(action="generate", type="EC", curve="INVALID")
        res = run_jwk_lab_logic(args)
        self.assertFalse(res)
        self.assertIn("Unsupported curve", mock_stderr.getvalue())
