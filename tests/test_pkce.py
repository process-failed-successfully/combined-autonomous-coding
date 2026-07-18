import unittest
import base64
import hashlib
import re
from shared.pkce_lab import PkceManager

class TestPkceManager(unittest.TestCase):
    def setUp(self):
        self.manager = PkceManager()

    def test_generate_verifier_length(self):
        verifier = self.manager.generate_verifier(43)
        self.assertEqual(len(verifier), 43)

        verifier = self.manager.generate_verifier(128)
        self.assertEqual(len(verifier), 128)

        with self.assertRaises(ValueError):
            self.manager.generate_verifier(42)

        with self.assertRaises(ValueError):
            self.manager.generate_verifier(129)

    def test_generate_verifier_characters(self):
        verifier = self.manager.generate_verifier(100)
        self.assertTrue(re.match(r'^[a-zA-Z0-9\-._~]+$', verifier), f"Invalid characters in verifier: {verifier}")

    def test_generate_challenge_s256(self):
        verifier = "my-test-verifier-which-is-long-enough-for-pkce"
        expected_hash = hashlib.sha256(verifier.encode('ascii')).digest()
        expected_challenge = base64.urlsafe_b64encode(expected_hash).decode('utf-8').rstrip('=')

        challenge = self.manager.generate_challenge(verifier, method="S256")
        self.assertEqual(challenge, expected_challenge)

        # Test case insensitivity for method
        challenge = self.manager.generate_challenge(verifier, method="s256")
        self.assertEqual(challenge, expected_challenge)

    def test_generate_challenge_plain(self):
        verifier = "my-test-verifier-which-is-long-enough-for-pkce"
        challenge = self.manager.generate_challenge(verifier, method="plain")
        self.assertEqual(challenge, verifier)

        challenge = self.manager.generate_challenge(verifier, method="PLAIN")
        self.assertEqual(challenge, verifier)

    def test_generate_challenge_invalid_method(self):
        verifier = "my-test-verifier"
        with self.assertRaises(ValueError):
            self.manager.generate_challenge(verifier, method="invalid")

    def test_verify_s256(self):
        verifier = self.manager.generate_verifier()
        challenge = self.manager.generate_challenge(verifier, method="S256")

        self.assertTrue(self.manager.verify(verifier, challenge, method="S256"))
        self.assertFalse(self.manager.verify(verifier, "wrong-challenge", method="S256"))
        self.assertFalse(self.manager.verify("wrong-verifier", challenge, method="S256"))

    def test_verify_plain(self):
        verifier = self.manager.generate_verifier()
        challenge = self.manager.generate_challenge(verifier, method="plain")

        self.assertTrue(self.manager.verify(verifier, challenge, method="plain"))
        self.assertFalse(self.manager.verify(verifier, "wrong-challenge", method="plain"))
        self.assertFalse(self.manager.verify("wrong-verifier", challenge, method="plain"))

if __name__ == '__main__':
    unittest.main()
