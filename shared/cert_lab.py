import sys
import ssl
import socket
import datetime
from pathlib import Path
from typing import Dict, Any, List
import ipaddress

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
except ImportError:
    # We will handle this gracefully if the module is missing at runtime
    x509 = None


class CertLabManager:
    """
    Manages Certificate operations: Inspect, Generate.
    """

    def __init__(self):
        if x509 is None:
            print("❌ Error: 'cryptography' library is required for Cert Lab.", file=sys.stderr)
            print("Please install it: pip install cryptography", file=sys.stderr)
            sys.exit(1)

    def get_cert_info(self, cert: x509.Certificate) -> Dict[str, Any]:
        """Extracts details from an x509 Certificate object."""

        # Subject
        subject_parts = []
        for attr in cert.subject:
            subject_parts.append(f"{attr.oid._name}={attr.value}")
        subject_str = ", ".join(subject_parts)

        # Issuer
        issuer_parts = []
        for attr in cert.issuer:
            issuer_parts.append(f"{attr.oid._name}={attr.value}")
        issuer_str = ", ".join(issuer_parts)

        # Validity
        not_before = cert.not_valid_before_utc
        not_after = cert.not_valid_after_utc
        now = datetime.datetime.now(datetime.timezone.utc)

        # Check if expired
        is_expired = now > not_after
        days_remaining = (not_after - now).days

        # SANs
        sans = []
        try:
            ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            sans = [str(n.value) for n in ext.value]
        except x509.ExtensionNotFound:
            pass

        # Fingerprint
        fingerprint = cert.fingerprint(hashes.SHA256()).hex()
        fingerprint_fmt = ":".join(fingerprint[i:i + 2] for i in range(0, len(fingerprint), 2))

        return {
            "subject": subject_str,
            "issuer": issuer_str,
            "serial_number": str(cert.serial_number),
            "version": cert.version.name,
            "valid_from": not_before.isoformat(),
            "valid_to": not_after.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": is_expired,
            "sans": sans,
            "fingerprint_sha256": fingerprint_fmt.upper()
        }

    def inspect_file(self, path: Path) -> Dict[str, Any]:
        """Loads and inspects a certificate from a file."""
        if not path.exists():
            return {"error": f"File not found: {path}"}

        try:
            data = path.read_bytes()
            # Try PEM
            try:
                cert = x509.load_pem_x509_certificate(data, default_backend())
            except ValueError:
                # Try DER
                try:
                    cert = x509.load_der_x509_certificate(data, default_backend())
                except ValueError:
                    return {"error": "Could not parse certificate (tried PEM and DER)."}

            return self.get_cert_info(cert)
        except Exception as e:
            return {"error": str(e)}

    def inspect_host(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Fetches and inspects a certificate from a remote host."""
        try:
            # We use get_server_certificate to get PEM, but it doesn't verify chain or handle SNI easily for all cases.
            # Better to use socket + ssl context.
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    der_data = ssock.getpeercert(binary_form=True)
                    if not der_data:
                        return {"error": "No certificate received from server."}

                    cert = x509.load_der_x509_certificate(der_data, default_backend())
                    return self.get_cert_info(cert)
        except Exception as e:
            return {"error": f"Connection failed: {e}"}

    def generate(self, cn: str, sans: List[str], days: int, output_dir: Path):
        """Generates a self-signed certificate."""
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ])

        issuer = subject  # Self-signed

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(key.public_key())
        builder = builder.serial_number(x509.random_serial_number())

        now = datetime.datetime.now(datetime.timezone.utc)
        builder = builder.not_valid_before(now)
        builder = builder.not_valid_after(now + datetime.timedelta(days=days))

        # Add SANs
        san_list = []
        # Always add CN as SAN for modern browsers if it's not already there
        if cn not in sans:
            sans.insert(0, cn)

        for s in sans:
            try:
                # Check if IP
                ip_obj = ipaddress.ip_address(s)
                san_list.append(x509.IPAddress(ip_obj))
            except ValueError:
                # DNS Name
                san_list.append(x509.DNSName(s))

        if san_list:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )

        cert = builder.sign(
            private_key=key, algorithm=hashes.SHA256(), backend=default_backend()
        )

        # Write files
        output_dir.mkdir(parents=True, exist_ok=True)
        key_path = output_dir / "key.pem"
        cert_path = output_dir / "cert.pem"

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        return key_path, cert_path


def run_cert_lab_logic(args) -> bool:
    """CLI Entry point."""
    manager = CertLabManager()

    if args.action == "inspect":
        source = args.source
        path = Path(source)

        # Heuristic: if file exists, treat as file. Else treat as host.
        if path.exists() and path.is_file():
            print(f"--- Inspecting File: {source} ---")
            info = manager.inspect_file(path)
        else:
            # Assume host[:port]
            if ":" in source:
                host, port_str = source.split(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    print(f"❌ Invalid port: {port_str}", file=sys.stderr)
                    return False
            else:
                host = source
                port = 443

            print(f"--- Inspecting Host: {host}:{port} ---")
            info = manager.inspect_host(host, port)

        if "error" in info:
            print(f"❌ {info['error']}", file=sys.stderr)
            return False

        # Print Info
        for k, v in info.items():
            key_display = k.replace("_", " ").title()
            if isinstance(v, list):
                val_display = ", ".join(v) if v else "(none)"
            else:
                val_display = v
            print(f"  {key_display:<20}: {val_display}")

        if info.get("is_expired"):
            print("\n❌ Certificate is EXPIRED!")
        elif info.get("days_remaining", 0) < 30:
            print(f"\n⚠️  Certificate expires soon ({info['days_remaining']} days)!")
        else:
            print("\n✅ Certificate is valid.")

        return True

    elif args.action == "generate":
        cn = args.cn
        output_dir = Path(args.output).resolve()
        days = args.days
        sans = [s.strip() for s in args.sans.split(",")] if args.sans else []

        print("--- Generating Certificate ---")
        print(f"  CN: {cn}")
        print(f"  SANs: {sans}")
        print(f"  Validity: {days} days")
        print(f"  Output: {output_dir}")

        try:
            key_path, cert_path = manager.generate(cn, sans, days, output_dir)
            print("\n✅ Successfully generated:")
            print(f"  - Key: {key_path}")
            print(f"  - Cert: {cert_path}")
            return True
        except Exception as e:
            print(f"❌ Generation failed: {e}", file=sys.stderr)
            return False

    return False
