import sys
import argparse

try:
    from sqids import Sqids
    HAS_SQIDS = True
except ImportError:
    HAS_SQIDS = False


class SqidsManager:
    """Manages Sqids encoding and decoding."""

    @staticmethod
    def encode(numbers: list[int]) -> str:
        if not HAS_SQIDS:
            raise ImportError("sqids module is not installed. Please install 'sqids' package.")
        sqids = Sqids()
        return sqids.encode(numbers)

    @staticmethod
    def decode(sqid_str: str) -> list[int]:
        if not HAS_SQIDS:
            raise ImportError("sqids module is not installed. Please install 'sqids' package.")
        sqids = Sqids()
        return sqids.decode(sqid_str)


def run_sqids_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for the Sqids Lab."""
    if not HAS_SQIDS:
        print("Error: The 'sqids' library is required for this command. Run 'pip install sqids'.", file=sys.stderr)
        return False

    # CLI encode
    if getattr(args, 'encode', None):
        try:
            numbers = [int(x.strip()) for x in args.encode.split(',')]
            encoded = SqidsManager.encode(numbers)
            print(encoded)
            return True
        except Exception as e:
            print(f"Sqids Encode Error: {e}", file=sys.stderr)
            return False

    # CLI decode
    elif getattr(args, 'decode', None):
        try:
            decoded = SqidsManager.decode(args.decode)
            if not decoded:
                print(f"Sqids Decode Error: Invalid sqid or no numbers decoded.", file=sys.stderr)
                return False
            print(",".join(str(n) for n in decoded))
            return True
        except Exception as e:
            print(f"Sqids Decode Error: {e}", file=sys.stderr)
            return False

    else:
        print("Error: Must provide either --encode or --decode flag unless using --tui.", file=sys.stderr)
        return False
