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

    def extract(self, text: str, unique: bool = False) -> List[str]:
        """Extracts all valid ULIDs from the given text."""
        import re
        # ULID format: 26 characters (0-9, A-H, J-K, M-N, P-T, V-Z)
        pattern = r'\b[0-9A-HJKMNP-TV-Z]{26}\b'
        matches = re.findall(pattern, text, re.IGNORECASE)

        valid_ulids = []
        for match in matches:
            # Reconstruct in uppercase as ULID strictly requires base32 character set
            upper_match = match.upper()
            if self.validate(upper_match):
                valid_ulids.append(upper_match)

        if unique:
            # Preserve order while making unique
            seen = set()
            unique_ulids = []
            for u in valid_ulids:
                if u not in seen:
                    unique_ulids.append(u)
                    seen.add(u)
            return unique_ulids

        return valid_ulids


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
        ulids = manager.extract(text_to_process, unique=unique)

        if not ulids:
            print("No ULIDs found.")
            sys.exit(0)

        for u in ulids:
            print(u)

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
