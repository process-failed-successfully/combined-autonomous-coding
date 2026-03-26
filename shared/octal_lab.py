import argparse
import sys


def octal_encode(data: bytes) -> str:
    """Encode bytes to a space-separated octal string."""
    return " ".join(f"{b:03o}" for b in data)


def octal_decode(s: str) -> bytes:
    """Decode a space-separated octal string to bytes."""
    s = s.strip()
    if not s:
        return b""
    try:
        parts = s.split()
        return bytes(int(p, 8) for p in parts)
    except ValueError as e:
        raise ValueError(f"Invalid octal string: {e}")


def run_octal_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None) is not None:
            text = args.encode.encode('utf-8')
            encoded = octal_encode(text)
            print(encoded)
        elif getattr(args, "decode", None) is not None:
            decoded = octal_decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing octal: {e}", file=sys.stderr)
        return False
