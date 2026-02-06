import sys
import ssl
import socket
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

class CertLabManager:
    """
    Manages Certificate Laboratory operations: inspection and generation.
    """

    @staticmethod
    def _parse_certificate(cert: x509.Certificate) -> Dict[str, Any]:
        """Helper to extract details from an X.509 certificate object."""
        try:
            subject = {}
            for attribute in cert.subject:
                # OID name (e.g. commonName) -> value
                key = attribute.oid._name
                subject[key] = attribute.value

            issuer = {}
            for attribute in cert.issuer:
                key = attribute.oid._name
                issuer[key] = attribute.value

            # Validity
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc

            # Remaining days
            now = datetime.datetime.now(datetime.timezone.utc)
            remaining = not_after - now
            days_remaining = remaining.days

            # SANs
            sans = []
            try:
                ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                sans = ext.value.get_values_for_type(x509.DNSName)
                # Add IPs if any
                sans.extend([str(ip) for ip in ext.value.get_values_for_type(x509.IPAddress)])
            except x509.ExtensionNotFound:
                pass

            return {
                "Subject": subject,
                "Issuer": issuer,
                "Serial Number": cert.serial_number,
                "Not Before": not_before.isoformat(),
                "Not After": not_after.isoformat(),
                "Days Remaining": days_remaining,
                "SANs": sans,
                "Fingerprint (SHA256)": cert.fingerprint(hashes.SHA256()).hex(),
                "Signature Algorithm": cert.signature_algorithm_oid._name
            }
        except Exception as e:
            raise ValueError(f"Error parsing certificate details: {e}")

    def inspect_file(self, path: Path) -> Dict[str, Any]:
        """Reads and inspects a local certificate file."""
        if not path.exists():
            raise FileNotFoundError(f"Certificate file not found: {path}")

        data = path.read_bytes()
        try:
            # Try loading as PEM
            cert = x509.load_pem_x509_certificate(data)
        except ValueError:
            try:
                # Try loading as DER
                cert = x509.load_der_x509_certificate(data)
            except ValueError:
                raise ValueError("Could not parse certificate (expected PEM or DER).")

        return self._parse_certificate(cert)

    def inspect_host(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Connects to a remote host and inspects its certificate."""
        try:
            # We use get_server_certificate to get the PEM string
            # Note: This doesn't validate the chain, just fetches the leaf cert.
            # For inspection purposes, this is usually what users want.
            cert_pem = ssl.get_server_certificate((host, port))
            cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'))
            return self._parse_certificate(cert)
        except (socket.error, ssl.SSLError) as e:
            raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")

    def generate_self_signed(self,
                             common_name: str,
                             sans: List[str],
                             days: int,
                             output_dir: Path) -> Tuple[Path, Path]:
        """
        Generates a self-signed certificate and private key.
        Returns paths to (cert_file, key_file).
        """
        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Subject and Issuer are the same for self-signed
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        # Build SANs
        alt_names = []
        for san in sans:
            # naive check for IP vs DNS
            # simple check: if it parses as int parts, treat as IP?
            # actually 'ipaddress' module is better but let's keep it simple and assume DNS for now
            # unless it looks very much like an IP.
            # Using shared/cidr_lab logic could help but let's just support DNS for simplicity or try/except ipaddress
            import ipaddress
            try:
                ip = ipaddress.ip_address(san)
                alt_names.append(x509.IPAddress(ip))
            except ValueError:
                alt_names.append(x509.DNSName(san))

        # Always include CN in SANs if not present (modern browsers require it)
        # But we only add it if user didn't specify it in SANs explicitly?
        # Actually standard practice is CN should be in SANs.

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(subject) # Self-signed
        builder = builder.public_key(key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        builder = builder.not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
        )

        if alt_names:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(alt_names),
                critical=False,
            )

        # Sign
        certificate = builder.sign(
            private_key=key, algorithm=hashes.SHA256()
        )

        # Ensure output dir exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filenames
        sanitized_cn = common_name.replace("*", "wildcard").replace(" ", "_").lower()
        cert_path = output_dir / f"{sanitized_cn}.crt"
        key_path = output_dir / f"{sanitized_cn}.key"

        # Write Cert
        with open(cert_path, "wb") as f:
            f.write(certificate.public_bytes(serialization.Encoding.PEM))

        # Write Key
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        return cert_path, key_path


def run_cert_lab_logic(args) -> bool:
    """CLI logic for cert-lab."""
    manager = CertLabManager()

    try:
        if args.action == "inspect":
            target = args.target
            # Check if file or host
            path = Path(target)
            if path.exists() and path.is_file():
                print(f"--- Inspecting File: {path} ---")
                details = manager.inspect_file(path)
            else:
                # Assume host:port
                if ":" in target:
                    host, port = target.split(":")
                    port = int(port)
                else:
                    host = target
                    port = 443
                print(f"--- Inspecting Host: {host}:{port} ---")
                details = manager.inspect_host(host, port)

            # Print Details
            print(f"Subject: {details['Subject']}")
            print(f"Issuer:  {details['Issuer']}")
            print(f"Serial:  {details['Serial Number']}")
            print(f"Validity: {details['Not Before']} to {details['Not After']}")

            # Color code days remaining
            days = details['Days Remaining']
            if days < 0:
                day_str = f"\033[91m{days} (EXPIRED)\033[0m"
            elif days < 30:
                day_str = f"\033[93m{days}\033[0m"
            else:
                day_str = f"\033[92m{days}\033[0m"
            print(f"Days Remaining: {day_str}")

            print(f"SANs:    {', '.join(details['SANs']) if details['SANs'] else 'None'}")
            print(f"Fingerprint: {details['Fingerprint (SHA256)']}")
            return True

        elif args.action == "generate":
            output_dir = Path(args.output) if args.output else Path(".")
            sans = args.san if args.san else []

            # Auto-add CN to SANs if list is empty, or just general good practice
            if not sans:
                sans = [args.common_name]

            print(f"Generating self-signed certificate for '{args.common_name}'...")
            cert_path, key_path = manager.generate_self_signed(
                common_name=args.common_name,
                sans=sans,
                days=args.days,
                output_dir=output_dir
            )
            print(f"✅ Generated certificate: {cert_path}")
            print(f"✅ Generated private key: {key_path}")
            return True

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

    return False
