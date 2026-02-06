import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.cert_lab import CertLabManager
from cryptography import x509
from cryptography.hazmat.primitives import serialization


class TestCertLab:

    @pytest.fixture
    def manager(self):
        return CertLabManager()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_generate_and_inspect_file(self, manager, temp_dir):
        cn = "test.local"
        sans = ["www.test.local", "127.0.0.1"]
        days = 10

        key_path, cert_path = manager.generate(cn, sans, days, temp_dir)

        assert key_path.exists()
        assert cert_path.exists()

        # Inspect
        info = manager.inspect_file(cert_path)

        assert "error" not in info
        # Cryptography uses 'commonName' for OID name
        assert f"commonName={cn}" in info["subject"]
        assert f"commonName={cn}" in info["issuer"]  # Self-signed
        assert "test.local" in info["sans"]  # CN is added to SANs
        assert "www.test.local" in info["sans"]
        assert "127.0.0.1" in info["sans"]
        assert info["days_remaining"] >= 9
        assert not info["is_expired"]

    @patch("socket.create_connection")
    @patch("ssl.create_default_context")
    def test_inspect_host(self, mock_ssl_ctx, mock_create_conn, manager, temp_dir):
        # Generate a real cert to use as mock data
        key_path, cert_path = manager.generate("remote.host", [], 365, temp_dir)
        cert_pem = cert_path.read_bytes()

        # Convert PEM to DER for the mock
        cert = x509.load_pem_x509_certificate(cert_pem)
        der_data = cert.public_bytes(encoding=serialization.Encoding.DER)

        # Mock Socket
        mock_sock = MagicMock()
        mock_create_conn.return_value.__enter__.return_value = mock_sock

        # Mock SSL Socket
        mock_ssock = MagicMock()
        mock_ssock.getpeercert.return_value = der_data

        # Mock Context
        mock_ctx_instance = MagicMock()
        mock_ssl_ctx.return_value = mock_ctx_instance
        mock_ctx_instance.wrap_socket.return_value.__enter__.return_value = mock_ssock

        info = manager.inspect_host("remote.host", 443)

        assert "error" not in info
        assert "commonName=remote.host" in info["subject"]

    def test_inspect_file_not_found(self, manager):
        info = manager.inspect_file(Path("nonexistent.crt"))
        assert "error" in info
        assert "File not found" in info["error"]
