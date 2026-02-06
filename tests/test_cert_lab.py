import unittest
import shutil
import tempfile
import sys
import os
from pathlib import Path
from io import StringIO
from unittest.mock import MagicMock, patch
from shared.cert_lab import CertLabManager, run_cert_lab_logic
import argparse

class TestCertLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = CertLabManager(self.test_dir)
        self.captured_out = StringIO()
        self.captured_err = StringIO()
        sys.stdout = self.captured_out
        sys.stderr = self.captured_err

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def test_generate_self_signed_cert(self):
        common_name = "test.local"
        key_path, crt_path = self.manager.generate_self_signed_cert(common_name, self.test_dir)

        self.assertTrue(key_path.exists())
        self.assertTrue(crt_path.exists())
        self.assertEqual(key_path.name, "test.local.key")
        self.assertEqual(crt_path.name, "test.local.crt")

        with open(crt_path, "r") as f:
            content = f.read()
            self.assertIn("BEGIN CERTIFICATE", content)
            self.assertIn("END CERTIFICATE", content)

    def test_inspect_local_cert(self):
        common_name = "test.inspect"
        _, crt_path = self.manager.generate_self_signed_cert(common_name, self.test_dir)

        self.manager.inspect_cert(str(crt_path))
        output = self.captured_out.getvalue()

        self.assertIn("Inspecting Local Certificate", output)
        self.assertIn(f"Subject: CN={common_name}", output)
        self.assertIn("Status: ✅ Valid", output)

    @patch("socket.create_connection")
    @patch("ssl.create_default_context")
    def test_inspect_remote_cert(self, mock_ssl_context, mock_create_connection):
        # Setup mock for remote cert
        common_name = "remote.test"
        _, crt_path = self.manager.generate_self_signed_cert(common_name, self.test_dir)
        with open(crt_path, "rb") as f:
            der_data = f.read() # This is PEM, we need DER for getpeercert(binary_form=True)
            # Actually, let's just generate a DER one or convert it
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            cert = x509.load_pem_x509_certificate(der_data, default_backend())
            der_bytes = cert.public_bytes(serialization.Encoding.DER)

        mock_socket = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_socket

        mock_ssl_sock = MagicMock()
        mock_ssl_context.return_value.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        mock_ssl_sock.getpeercert.return_value = der_bytes

        self.manager.inspect_cert("example.com:443")

        output = self.captured_out.getvalue()
        self.assertIn("Inspecting Remote Certificate: example.com:443", output)
        self.assertIn(f"Subject: CN={common_name}", output)

    def test_cli_generate(self):
        args = argparse.Namespace(
            action="generate",
            common_name="cli.test",
            output=str(self.test_dir),
            project_dir=str(self.test_dir)
        )

        with self.assertRaises(SystemExit) as cm:
            run_cert_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.test_dir / "cli.test.key").exists())
        self.assertTrue((self.test_dir / "cli.test.crt").exists())

if __name__ == "__main__":
    unittest.main()
