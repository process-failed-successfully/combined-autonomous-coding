import unittest
import shutil
import tempfile
import sys
import os
import ssl
import socket
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.cert_lab import CertLabManager, run_cert_lab_logic
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID

class TestCertLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = CertLabManager()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_self_signed(self):
        cert_path, key_path = self.manager.generate_self_signed(
            common_name="test.local",
            sans=["test.local", "127.0.0.1"],
            days=10,
            output_dir=self.test_dir
        )

        self.assertTrue(cert_path.exists())
        self.assertTrue(key_path.exists())
        self.assertEqual(cert_path.name, "test.local.crt")
        self.assertEqual(key_path.name, "test.local.key")

        # Verify content
        cert_bytes = cert_path.read_bytes()
        cert = x509.load_pem_x509_certificate(cert_bytes)

        subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        self.assertEqual(subject_cn, "test.local")

    def test_inspect_file(self):
        # Generate first
        cert_path, _ = self.manager.generate_self_signed(
            common_name="inspect.me",
            sans=["inspect.me"],
            days=30,
            output_dir=self.test_dir
        )

        details = self.manager.inspect_file(cert_path)

        self.assertEqual(details['Subject']['commonName'], "inspect.me")
        self.assertEqual(details['Issuer']['commonName'], "inspect.me") # Self-signed
        self.assertIn("inspect.me", details['SANs'])
        self.assertTrue(details['Days Remaining'] >= 29)

    @patch('ssl.get_server_certificate')
    def test_inspect_host(self, mock_get_cert):
        # Create a real cert to return as PEM string
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "remote.host")])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            subject
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).sign(key, hashes.SHA256())

        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        mock_get_cert.return_value = cert_pem

        details = self.manager.inspect_host("remote.host", 443)

        self.assertEqual(details['Subject']['commonName'], "remote.host")
        mock_get_cert.assert_called_with(("remote.host", 443))

    def test_cli_inspect_file(self):
        # Generate cert
        cert_path, _ = self.manager.generate_self_signed(
            common_name="cli.test",
            sans=[],
            days=1,
            output_dir=self.test_dir
        )

        args = MagicMock()
        args.action = "inspect"
        args.target = str(cert_path)

        # Capture stdout
        from io import StringIO
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            success = run_cert_lab_logic(args)
            output = out.getvalue()
        finally:
            sys.stdout = saved_stdout

        self.assertTrue(success)
        self.assertIn("Subject: {'commonName': 'cli.test'}", output)

if __name__ == '__main__':
    unittest.main()
