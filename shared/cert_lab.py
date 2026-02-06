import sys
import ssl
import socket
import datetime
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class CertLabManager:
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or Path(".")

    def generate_self_signed_cert(self, common_name, output_dir=None):
        """Generates a self-signed certificate and private key."""
        output_dir = output_dir or self.project_dir
        key_path = output_dir / f"{common_name}.key"
        crt_path = output_dir / f"{common_name}.crt"

        # Generate Key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Generate Cert
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(key, hashes.SHA256(), default_backend())

        # Write Key
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        # Write Cert
        with open(crt_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        return key_path, crt_path

    def inspect_cert(self, target):
        """Inspects a certificate (local file or remote host)."""
        target_path = Path(target)
        if target_path.exists() and target_path.is_file():
            self._inspect_local(target_path)
        else:
            # Assume host:port or host (default port 443)
            if ":" in target:
                host, port = target.split(":")
                port = int(port)
            else:
                host, port = target, 443
            self._inspect_remote(host, port)

    def _inspect_local(self, path):
        print(f"--- Inspecting Local Certificate: {path} ---")
        try:
            with open(path, "rb") as f:
                pem_data = f.read()
            cert = x509.load_pem_x509_certificate(pem_data, default_backend())
            self._print_cert_details(cert)
        except Exception as e:
            print(f"❌ Error parsing certificate: {e}", file=sys.stderr)

    def _inspect_remote(self, host, port):
        print(f"--- Inspecting Remote Certificate: {host}:{port} ---")
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    if not der_cert:
                         print("❌ No certificate provided by peer.", file=sys.stderr)
                         return

                    cert = x509.load_der_x509_certificate(der_cert, default_backend())
                    self._print_cert_details(cert)

        except Exception as e:
            print(f"❌ Error connecting to {host}:{port}: {e}", file=sys.stderr)

    def _print_cert_details(self, cert):
        print(f"Subject: {cert.subject.rfc4514_string()}")
        print(f"Issuer:  {cert.issuer.rfc4514_string()}")
        print(f"Serial:  {cert.serial_number}")
        print(f"Valid From: {cert.not_valid_before_utc}")
        print(f"Valid Until: {cert.not_valid_after_utc}")

        # Check expiry
        now = datetime.datetime.now(datetime.timezone.utc)
        if now > cert.not_valid_after_utc:
            print("Status: ❌ EXPIRED")
        elif now < cert.not_valid_before_utc:
            print("Status: ❌ NOT YET VALID")
        else:
            days_left = (cert.not_valid_after_utc - now).days
            print(f"Status: ✅ Valid ({days_left} days remaining)")

        # Print SANs if available
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            print("SANs:")
            for name in san.value:
                print(f"  - {name.value}")
        except x509.ExtensionNotFound:
            pass

def run_cert_lab_logic(args):
    """Entry point for CLI."""
    manager = CertLabManager(Path(args.project_dir) if hasattr(args, 'project_dir') else Path("."))

    if args.action == "generate":
        if not args.common_name:
            print("Error: Common Name is required.", file=sys.stderr)
            sys.exit(1)

        out_dir = Path(args.output) if args.output else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)

        try:
            key, crt = manager.generate_self_signed_cert(args.common_name, out_dir)
            print(f"✅ Generated certificate and key:")
            print(f"  - {crt}")
            print(f"  - {key}")
        except Exception as e:
            print(f"❌ Error generating certificate: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "inspect":
        if not args.target:
            print("Error: Target (file or host:port) is required.", file=sys.stderr)
            sys.exit(1)
        manager.inspect_cert(args.target)

    sys.exit(0)
