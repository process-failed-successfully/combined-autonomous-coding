import argparse
import sys


def punycode_encode(domain: str) -> str:
    """Encodes a Unicode domain to Punycode/IDN format."""
    try:
        return domain.encode('idna').decode('ascii')
    except Exception as e:
        raise ValueError(f"Failed to encode domain: {e}")


def punycode_decode(punycode_domain: str) -> str:
    """Decodes a Punycode/IDN domain back to Unicode."""
    try:
        return punycode_domain.encode('ascii').decode('idna')
    except Exception as e:
        raise ValueError(f"Failed to decode domain: {e}")


def run_punycode_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for the punycode-lab command."""
    try:
        if getattr(args, "encode", None):
            result = punycode_encode(args.encode)
            print(result)
        elif getattr(args, "decode", None):
            result = punycode_decode(args.decode)
            print(result)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing punycode: {e}", file=sys.stderr)
        return False
