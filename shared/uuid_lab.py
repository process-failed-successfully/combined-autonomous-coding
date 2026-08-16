import uuid
import sys
from typing import List, Dict, Any, Optional

class UuidLabManager:
    """Manages UUID operations (generation, inspection, validation)."""

    def generate(self, version: int = 4, count: int = 1, namespace: str = None, name: str = None) -> List[str]:
        """Generates UUIDs."""
        results = []
        ns_uuid = None

        if version in [3, 5]:
            if not name:
                raise ValueError("Name is required for UUID v3 and v5.")

            if namespace:
                 # Check for predefined namespaces
                 upper_ns = namespace.upper()
                 if hasattr(uuid, f"NAMESPACE_{upper_ns}"):
                     ns_uuid = getattr(uuid, f"NAMESPACE_{upper_ns}")
                 else:
                     try:
                         ns_uuid = uuid.UUID(namespace)
                     except ValueError:
                         raise ValueError(f"Invalid namespace UUID: {namespace}")
            else:
                 ns_uuid = uuid.NAMESPACE_DNS # Default to DNS

        for _ in range(count):
            if version == 1:
                u = uuid.uuid1()
            elif version == 3:
                u = uuid.uuid3(ns_uuid, name)
            elif version == 4:
                u = uuid.uuid4()
            elif version == 5:
                u = uuid.uuid5(ns_uuid, name)
            elif version == 7:
                import time
                import os
                t_ms = int(time.time() * 1000)
                t_bytes = t_ms.to_bytes(6, 'big')
                rand = os.urandom(10)
                b = bytearray(16)
                b[0:6] = t_bytes
                b[6] = 0x70 | (rand[0] & 0x0f)
                b[7] = rand[1]
                b[8] = 0x80 | (rand[2] & 0x3f)
                b[9:] = rand[3:10]
                u = uuid.UUID(bytes=bytes(b))
            else:
                raise ValueError(f"Unsupported UUID version: {version}")

            results.append(str(u))

        return results

    def inspect(self, uuid_str: str) -> Dict[str, Any]:
        """Decodes and inspects a UUID."""
        try:
            u = uuid.UUID(uuid_str)
        except ValueError:
            return {"valid": False, "error": "Invalid UUID format"}

        info = {
            "valid": True,
            "uuid": str(u),
            "version": u.version,
            "variant": u.variant,
            "hex": u.hex,
            "int": u.int,
            "urn": u.urn,
        }

        if u.version == 1:
            # Time is 100-nanosecond intervals since 1582-10-15
            info["time"] = u.time
            info["clock_seq"] = u.clock_seq
            info["node"] = u.node
            # MAC address formatting
            info["mac"] = ':'.join(['{:02x}'.format((u.node >> ele) & 0xff) for ele in range(40, -1, -8)])

            # Convert to ISO timestamp
            # 0x01b21dd213814000 is the number of 100-ns intervals between
            # 1582-10-15 and 1970-01-01
            try:
                ts = (u.time - 0x01b21dd213814000) / 1e7
                from datetime import datetime
                info["timestamp_iso"] = datetime.fromtimestamp(ts).isoformat()
            except Exception:
                pass

        elif u.version == 7:
            # Time is 48-bit Unix Epoch in milliseconds
            time_ms = int.from_bytes(u.bytes[:6], 'big')
            info["time_ms"] = time_ms
            try:
                from datetime import datetime
                info["timestamp_iso"] = datetime.fromtimestamp(time_ms / 1000.0).isoformat()
            except Exception:
                pass

        return info

    def validate(self, uuid_str: str) -> bool:
        """Checks if a string is a valid UUID."""
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False

    def format(self, uuid_str: str, format_type: str = "standard") -> str:
        """Formats a UUID into a specific string representation."""
        try:
            u = uuid.UUID(uuid_str)
        except ValueError:
            raise ValueError(f"Invalid UUID: {uuid_str}")

        if format_type == "standard":
            return str(u)
        elif format_type == "hex":
            return u.hex
        elif format_type == "urn":
            return u.urn
        elif format_type == "int":
            return str(u.int)
        elif format_type == "base64":
            import base64
            return base64.b64encode(u.bytes).decode('ascii')
        elif format_type == "base64url":
            import base64
            return base64.urlsafe_b64encode(u.bytes).decode('ascii').rstrip('=')
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def extract(self, text: str, unique: bool = False) -> List[str]:
        """Extracts all valid UUIDs from the given text."""
        import re
        # UUID v1-v5 format regex
        pattern = r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b'
        matches = re.findall(pattern, text)

        # Verify valid UUIDs (just in case)
        valid_uuids = []
        for match in matches:
            if self.validate(match):
                # Standardize to lowercase
                standardized = str(uuid.UUID(match)).lower()
                valid_uuids.append(standardized)

        if unique:
            # Preserve order while making unique
            seen = set()
            unique_uuids = []
            for u in valid_uuids:
                if u not in seen:
                    unique_uuids.append(u)
                    seen.add(u)
            return unique_uuids

        return valid_uuids

def run_uuid_lab_logic(args):
    """CLI handler for UUID Lab."""
    manager = UuidLabManager()

    # Handle version argument which might be a string or int from argparse
    version = int(args.version) if hasattr(args, 'version') and args.version else 4

    if args.action == "generate":
        try:
            results = manager.generate(
                version=version,
                count=args.count,
                namespace=getattr(args, 'namespace', None),
                name=getattr(args, 'name', None)
            )
            for res in results:
                print(res)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "inspect":
        info = manager.inspect(args.uuid)
        if not info["valid"]:
            print(f"Error: {info['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"--- UUID Inspection: {args.uuid} ---")
        print(f"  Valid:   {info['valid']}")
        print(f"  Version: {info['version']}")
        print(f"  Variant: {info['variant']}")
        print(f"  Hex:     {info['hex']}")
        print(f"  Int:     {info['int']}")
        print(f"  URN:     {info['urn']}")

        if info.get("version") == 1:
             print(f"  Time:    {info['time']} (100-ns intervals since 1582-10-15)")
             if "timestamp_iso" in info:
                 print(f"  Date:    {info['timestamp_iso']}")
             print(f"  Clock:   {info['clock_seq']}")
             print(f"  Node:    {info['node']}")
             print(f"  MAC:     {info['mac']}")

        elif info.get("version") == 7:
             print(f"  Time MS: {info.get('time_ms')} (Unix Epoch)")
             if "timestamp_iso" in info:
                 print(f"  Date:    {info['timestamp_iso']}")

    elif args.action in ("format", "fmt"):
        try:
            formatted = manager.format(args.uuid, format_type=getattr(args, 'type', 'standard'))
            print(formatted)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        if manager.validate(args.uuid):
            print(f"✅ Valid UUID: {args.uuid}")
            sys.exit(0)
        else:
            print(f"❌ Invalid UUID: {args.uuid}")
            sys.exit(1)

    elif args.action == "bulk":
        try:
             results = manager.generate(version=version, count=args.count)
             for res in results:
                 print(res)
        except Exception as e:
             print(f"Error: {e}", file=sys.stderr)
             sys.exit(1)

    elif args.action == "extract":
        text_to_process = ""
        if hasattr(args, 'file') and args.file:
            from pathlib import Path
            try:
                text_to_process = Path(args.file).read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        elif hasattr(args, 'text') and args.text:
            text_to_process = args.text
        elif not sys.stdin.isatty():
            text_to_process = sys.stdin.read()
        else:
            print("Error: Provide text via --text, --file, or stdin.", file=sys.stderr)
            sys.exit(1)

        unique = getattr(args, 'unique', False)
        uuids = manager.extract(text_to_process, unique=unique)

        if not uuids:
            print("No UUIDs found.")
            sys.exit(0)

        for u in uuids:
            print(u)
