import ulid
import sys
from typing import List, Dict, Any


class UlidLabManager:
    """Manages ULID operations (generation, inspection, validation)."""

    def generate(self, count: int = 1) -> List[str]:
        """Generates ULIDs."""
        results = []
        for _ in range(count):
            u = ulid.new()
            results.append(u.str)
        return results

    def inspect(self, ulid_str: str) -> Dict[str, Any]:
        """Decodes and inspects a ULID."""
        try:
            u = ulid.parse(ulid_str)
        except ValueError:
            return {"valid": False, "error": "Invalid ULID format"}

        return {
            "valid": True,
            "ulid": u.str,
            "timestamp": u.timestamp().int,
            "datetime": u.timestamp().datetime.isoformat(),
            "randomness": u.randomness().str,
            "hex": u.hex,
            "int": u.int,
            "bytes": u.bytes.hex(),
            "uuid": u.uuid.hex
        }

    def validate(self, ulid_str: str) -> bool:
        """Checks if a string is a valid ULID."""
        try:
            ulid.parse(ulid_str)
            return True
        except ValueError:
            return False


def run_ulid_lab_logic(args):
    """CLI handler for ULID Lab."""
    manager = UlidLabManager()

    if args.action == "generate":
        try:
            results = manager.generate(count=args.count)
            for res in results:
                print(res)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "inspect":
        if not args.ulid:
            print("Error: --ulid is required for inspect action.", file=sys.stderr)
            sys.exit(1)

        info = manager.inspect(args.ulid)
        if not info["valid"]:
            print(f"Error: {info['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"--- ULID Inspection: {args.ulid} ---")
        print(f"  Valid:      {info['valid']}")
        print(f"  ULID:       {info['ulid']}")
        print(f"  Timestamp:  {info['timestamp']}")
        print(f"  Date:       {info['datetime']}")
        print(f"  Randomness: {info['randomness']}")
        print(f"  Hex:        {info['hex']}")
        print(f"  Int:        {info['int']}")
        print(f"  UUID:       {info['uuid']}")

    elif args.action == "validate":
        if not args.ulid:
            print("Error: --ulid is required for validate action.", file=sys.stderr)
            sys.exit(1)

        if manager.validate(args.ulid):
            print(f"✅ Valid ULID: {args.ulid}")
            sys.exit(0)
        else:
            print(f"❌ Invalid ULID: {args.ulid}")
            sys.exit(1)

    elif args.action == "bulk":
        try:
            results = manager.generate(count=args.count)
            for res in results:
                print(res)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
