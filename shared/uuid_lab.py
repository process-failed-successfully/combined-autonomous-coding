import uuid
import sys
from typing import List, Dict, Any, Optional


class UuidLabManager:
    """Manages UUID operations (generation, inspection, validation)."""

    def generate(self, version: int = 4, count: int = 1, namespace: Optional[str] = None, name: Optional[str] = None) -> List[str]:
        """Generates UUIDs."""
        results = []
        ns_uuid: Optional[uuid.UUID] = None

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
                ns_uuid = uuid.NAMESPACE_DNS  # Default to DNS

        for _ in range(count):
            if version == 1:
                u = uuid.uuid1()
            elif version == 3:
                # uuid3 expects a UUID as first argument
                if ns_uuid is None:
                    # This should not happen due to logic above, but for mypy:
                    raise ValueError("Namespace UUID is required for v3")
                u = uuid.uuid3(ns_uuid, name)  # type: ignore # name is str, should be fine
            elif version == 4:
                u = uuid.uuid4()
            elif version == 5:
                # uuid5 expects a UUID as first argument
                if ns_uuid is None:
                    raise ValueError("Namespace UUID is required for v5")
                u = uuid.uuid5(ns_uuid, name)  # type: ignore
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

        return info

    def validate(self, uuid_str: str) -> bool:
        """Checks if a string is a valid UUID."""
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False


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
