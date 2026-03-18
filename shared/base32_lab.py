import argparse
import base64
import sys


def run_base32_lab_logic(args: argparse.Namespace) -> bool:
    try:
        use_hex = getattr(args, "hex", False)

        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            if use_hex:
                encoded = base64.b32hexencode(text).decode('utf-8')
            else:
                encoded = base64.b32encode(text).decode('utf-8')
            print(encoded)
        elif getattr(args, "decode", None):
            if use_hex:
                decoded = base64.b32hexdecode(args.decode, casefold=True).decode('utf-8')
            else:
                decoded = base64.b32decode(args.decode, casefold=True).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base32: {e}", file=sys.stderr)
        return False
