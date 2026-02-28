"""
MAC Address Lab
===============

Utilities for generating, formatting, validating, and looking up MAC addresses.
"""

import sys
import re
import random
import urllib.request
import urllib.error
import json
from typing import List, Optional

class MacLabManager:
    """Manages MAC address operations."""

    def validate(self, mac: str) -> bool:
        """Validates if a string is a MAC address."""
        # Remove common separators
        cleaned = re.sub(r'[:-]', '', mac).strip()
        # Also handles dot notation like aaaa.bbbb.cccc by removing dots
        cleaned = cleaned.replace('.', '')

        if len(cleaned) != 12:
            return False

        try:
            int(cleaned, 16)
            return True
        except ValueError:
            return False

    def format_mac(self, mac: str, uppercase: bool = False, separator: str = ":") -> str:
        """Formats a MAC address with specified separator and case."""
        if not self.validate(mac):
            raise ValueError(f"Invalid MAC address: {mac}")

        cleaned = re.sub(r'[:\-.]', '', mac).strip().lower()

        if separator == ".":
            # Cisco style aaaa.bbbb.cccc
            parts = [cleaned[i:i+4] for i in range(0, 12, 4)]
        else:
            # Standard aa:bb:cc:dd:ee:ff
            parts = [cleaned[i:i+2] for i in range(0, 12, 2)]

        result = separator.join(parts)
        if uppercase:
            return result.upper()
        return result

    def generate(self, count: int = 1, prefix: Optional[str] = None, uppercase: bool = False, separator: str = ":") -> List[str]:
        """Generates random MAC addresses."""
        results = []

        for _ in range(count):
            mac_parts = []

            if prefix:
                if not self.validate(prefix + "000000"[:12-len(re.sub(r'[:\-.]', '', prefix))]):
                     raise ValueError(f"Invalid MAC prefix: {prefix}")

                clean_prefix = re.sub(r'[:\-.]', '', prefix).lower()
                # If odd length, we pad it with a random nibble or just take the even parts?
                # Let's assume the user provides full hex pairs e.g. "00:1A:2B"
                for i in range(0, len(clean_prefix), 2):
                    if i + 1 < len(clean_prefix):
                        mac_parts.append(clean_prefix[i:i+2])
                    else:
                        mac_parts.append(clean_prefix[i] + random.choice('0123456789abcdef'))

            # Fill the rest
            while len(mac_parts) < 6:
                # First octet needs to be locally administered and unicast if no prefix
                if not mac_parts and not prefix:
                    # Locally administered: x2, x6, xA, xE
                    first_byte = random.choice('0123456789abcdef') + random.choice('26ae')
                    mac_parts.append(first_byte)
                else:
                    mac_parts.append(f"{random.randint(0, 255):02x}")

            raw_mac = "".join(mac_parts)[:12]
            results.append(self.format_mac(raw_mac, uppercase, separator))

        return results

    def lookup(self, mac: str) -> dict:
        """Looks up the vendor of a MAC address via macvendors.co API."""
        if not self.validate(mac):
            raise ValueError(f"Invalid MAC address: {mac}")

        url = f"https://macvendors.co/api/{mac}"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CombinedAutonomousCodingAgent/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
                data = json.loads(response.read().decode())

            if "result" in data and "error" not in data["result"]:
                return {
                    "mac": mac,
                    "company": data["result"].get("company", "Unknown"),
                    "mac_prefix": data["result"].get("mac_prefix", ""),
                    "address": data["result"].get("address", "")
                }
            else:
                return {
                    "mac": mac,
                    "company": "Not Found",
                    "error": data.get("result", {}).get("error", "Unknown error")
                }
        except urllib.error.URLError as e:
             return {
                 "mac": mac,
                 "company": "Error",
                 "error": f"Failed to connect to lookup service: {e}"
             }
        except Exception as e:
             return {
                 "mac": mac,
                 "company": "Error",
                 "error": str(e)
             }

def run_mac_lab_logic(args):
    """CLI logic for MAC Lab."""
    manager = MacLabManager()

    if args.action == "generate":
        try:
            macs = manager.generate(
                count=args.count,
                prefix=args.prefix,
                uppercase=args.upper,
                separator=args.separator
            )
            for m in macs:
                print(m)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "format":
        if not args.mac:
            print("Error: --mac is required for format action.", file=sys.stderr)
            sys.exit(1)
        try:
            print(manager.format_mac(args.mac, args.upper, args.separator))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        if not args.mac:
            print("Error: --mac is required for validate action.", file=sys.stderr)
            sys.exit(1)
        is_valid = manager.validate(args.mac)
        if is_valid:
            print(f"✅ {args.mac} is a VALID MAC address.")
            sys.exit(0)
        else:
            print(f"❌ {args.mac} is an INVALID MAC address.")
            sys.exit(1)

    elif args.action == "lookup":
        if not args.mac:
            print("Error: --mac is required for lookup action.", file=sys.stderr)
            sys.exit(1)

        print(f"Looking up vendor for {args.mac}...")
        try:
            result = manager.lookup(args.mac)
            print("-" * 30)
            print(f"MAC:     {result['mac']}")
            print(f"Vendor:  {result.get('company')}")
            if result.get('address'):
                print(f"Address: {result.get('address')}")
            if result.get('error'):
                print(f"Error:   {result.get('error')}")
            print("-" * 30)
        except ValueError as e:
             print(f"Error: {e}", file=sys.stderr)
             sys.exit(1)

    sys.exit(0)
