import random
import re
import sys
import argparse
from typing import List, Dict, Any, Optional
import urllib.request
import json
import ssl

class MacLabManager:
    """Manages MAC address operations (generation, formatting, validation, lookup)."""

    def generate(self, count: int = 1, prefix: str = "", format: str = "colon") -> List[str]:
        """Generates random MAC addresses."""
        results = []

        # Parse prefix if provided
        prefix_bytes = []
        if prefix:
            # Clean up the prefix
            clean_prefix = re.sub(r'[^0-9a-fA-F]', '', prefix)
            if len(clean_prefix) % 2 != 0:
                raise ValueError("Prefix must contain an even number of hex digits.")
            if len(clean_prefix) > 12:
                raise ValueError("Prefix cannot exceed 12 hex digits (6 bytes).")

            for i in range(0, len(clean_prefix), 2):
                prefix_bytes.append(int(clean_prefix[i:i+2], 16))

        for _ in range(count):
            mac_bytes = prefix_bytes.copy()
            while len(mac_bytes) < 6:
                mac_bytes.append(random.randint(0x00, 0xff))

            # Ensure it's a unicast, globally unique address if no prefix was provided
            # (clearing the multicast and locally administered bits)
            if not prefix:
                mac_bytes[0] &= 0xfc

            results.append(self._format_mac(mac_bytes, format))

        return results

    def _format_mac(self, mac_bytes: List[int], fmt: str) -> str:
        """Formats MAC address bytes into the specified string format."""
        if fmt == "colon":
            return ":".join(f"{b:02x}" for b in mac_bytes)
        elif fmt == "hyphen":
            return "-".join(f"{b:02x}" for b in mac_bytes)
        elif fmt == "dot":
            hex_str = "".join(f"{b:02x}" for b in mac_bytes)
            return f"{hex_str[0:4]}.{hex_str[4:8]}.{hex_str[8:12]}"
        elif fmt == "plain":
            return "".join(f"{b:02x}" for b in mac_bytes)
        else:
            raise ValueError(f"Unknown format: {fmt}")

    def format(self, mac: str, fmt: str) -> str:
        """Reformats a MAC address."""
        clean_mac = re.sub(r'[^0-9a-fA-F]', '', mac)
        if len(clean_mac) != 12:
            raise ValueError(f"Invalid MAC address length: {mac}")

        mac_bytes = [int(clean_mac[i:i+2], 16) for i in range(0, 12, 2)]
        return self._format_mac(mac_bytes, fmt)

    def validate(self, mac: str) -> bool:
        """Checks if a string is a valid MAC address."""
        # Check standard formats
        if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
            return True
        if re.match(r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$', mac):
            return True
        if re.match(r'^[0-9A-Fa-f]{12}$', mac):
            return True
        return False

    def lookup(self, mac: str) -> Dict[str, Any]:
        """Looks up the vendor of a MAC address using maclookup.app API."""
        if not self.validate(mac):
            return {"valid": False, "error": "Invalid MAC address format"}

        clean_mac = re.sub(r'[^0-9a-fA-F]', '', mac)
        prefix = clean_mac[:6].upper()

        info = {
            "valid": True,
            "mac": self.format(mac, "colon"),
            "prefix": prefix,
            "vendor": "Unknown"
        }

        # Use an open API for MAC lookup (maclookup.app)
        url = f"https://api.maclookup.app/v2/macs/{prefix}"

        try:
            # Create a context that doesn't verify SSL if there are local cert issues
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get("success") and data.get("found"):
                        info["vendor"] = data.get("company", "Unknown")
                        info["company"] = data.get("company", "Unknown")
                        info["country"] = data.get("country", "")
                        info["address"] = data.get("address", "")
        except Exception as e:
            info["error"] = f"Lookup failed: {str(e)}"

        return info


def run_mac_lab_logic(args: argparse.Namespace):
    """CLI handler for Mac Lab."""
    manager = MacLabManager()

    if args.action == "generate":
        try:
            results = manager.generate(
                count=args.count,
                prefix=getattr(args, 'prefix', ""),
                format=args.format
            )
            for res in results:
                print(res)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "format":
        try:
            print(manager.format(args.mac, args.format))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        if manager.validate(args.mac):
            print(f"✅ Valid MAC Address: {args.mac}")
            sys.exit(0)
        else:
            print(f"❌ Invalid MAC Address: {args.mac}")
            sys.exit(1)

    elif args.action == "lookup":
        info = manager.lookup(args.mac)

        if not info["valid"]:
            print(f"Error: {info['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"--- MAC Lookup: {info['mac']} ---")
        print(f"  Prefix: {info['prefix']}")
        print(f"  Vendor: {info['vendor']}")

        if info.get("country"):
            print(f"  Country: {info['country']}")
        if info.get("address"):
            print(f"  Address: {info['address']}")

        if "error" in info:
            print(f"\n  Note: {info['error']}")
