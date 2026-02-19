import base64
import hmac
import struct
import time
import sys
import secrets
import hashlib
import urllib.parse
from typing import Optional


class OtpLabManager:
    """
    Manages One-Time Password (OTP) operations: generate secret, code, verify, url.
    Supports TOTP (Time-based) and HOTP (HMAC-based).
    """

    def generate_secret(self, length: int = 16) -> str:
        """
        Generates a random Base32 secret string.
        Standard length is 16 chars (10 bytes -> 16 base32 chars).
        """
        # 16 chars of base32 is 10 bytes (16 * 5 bits = 80 bits = 10 bytes)
        # RFC 4226 recommends 160 bits (20 bytes) for secret.
        # Each base32 char is 5 bits. length * 5 / 8 bytes.
        num_bytes = (length * 5) // 8
        random_bytes = secrets.token_bytes(num_bytes)
        # Remove padding '=' for cleaner output, though some apps might need it (usually not).
        return base64.b32encode(random_bytes).decode('utf-8')[:length]

    def generate_hotp(self, secret: str, counter: int, digits: int = 6, digest: str = 'sha1') -> str:
        """
        Generates an HMAC-based One-Time Password (HOTP) code.
        """
        try:
            # Padding might be missing, add it just in case
            padding = '=' * ((8 - len(secret) % 8) % 8)
            key = base64.b32decode(secret.upper() + padding, casefold=True)
        except Exception as e:
            raise ValueError(f"Invalid Base32 secret: {e}")

        msg = struct.pack(">Q", counter)
        digest_module = getattr(hashlib, digest.lower())
        h = hmac.new(key, msg, digest_module).digest()

        # Dynamic truncation
        offset = h[-1] & 0x0f
        binary = struct.unpack(">I", h[offset:offset+4])[0] & 0x7fffffff
        code = binary % (10 ** digits)

        return str(code).zfill(digits)

    def generate_totp(self, secret: str, interval: int = 30, digits: int = 6, timestamp: Optional[float] = None) -> str:
        """
        Generates a Time-based One-Time Password (TOTP) code.
        """
        if timestamp is None:
            timestamp = time.time()
        counter = int(timestamp / interval)
        return self.generate_hotp(secret, counter, digits=digits)

    def verify_totp(self, secret: str, code: str, interval: int = 30, window: int = 1, digits: int = 6) -> bool:
        """
        Verifies a TOTP code within a time window.
        window: number of intervals to check before and after current time.
        """
        now = time.time()
        counter = int(now / interval)

        # Check current, previous, and next intervals based on window
        # We check current first, then +/- 1, then +/- 2 etc.
        # Actually checking range is fine.

        # To avoid timing attacks, we should technically check all and return constant time,
        # but for this CLI tool, breaking early on success is acceptable (it's not a server verifier).
        # Wait, if I want to be secure, I should use hmac.compare_digest.

        for i in range(-window, window + 1):
            check_counter = counter + i
            generated = self.generate_hotp(secret, check_counter, digits=digits)
            if hmac.compare_digest(generated, code):
                return True
        return False

    def generate_url(self, secret: str, label: str, issuer: Optional[str] = None, digits: int = 6, period: int = 30) -> str:
        """
        Generates a otpauth:// URL for QR codes.
        """
        params = {
            "secret": secret.upper(),
            "digits": digits,
            "period": period,
            "algorithm": "SHA1"  # Default
        }

        if issuer:
            params["issuer"] = issuer
            if ":" not in label:
                label = f"{issuer}:{label}"

        # Quote the label
        encoded_label = urllib.parse.quote(label)

        base_url = f"otpauth://totp/{encoded_label}"
        query_string = urllib.parse.urlencode(params)

        return f"{base_url}?{query_string}"


def run_otp_lab_logic(args):
    """
    CLI handler for OTP Lab.
    """
    manager = OtpLabManager()

    if args.action == "generate":
        secret = manager.generate_secret(args.length)
        print(f"Secret: {secret}")
        print("(Base32 encoded)")

    elif args.action == "code":
        try:
            code = manager.generate_totp(
                args.secret,
                interval=args.interval,
                digits=args.digits
            )
            print(code)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "verify":
        try:
            valid = manager.verify_totp(
                args.secret,
                args.code,
                window=args.window
            )
            if valid:
                print("✅ Code is VALID.")
                sys.exit(0)
            else:
                print("❌ Code is INVALID.")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "url":
        url = manager.generate_url(
            args.secret,
            args.label,
            issuer=args.issuer
        )
        print(url)
