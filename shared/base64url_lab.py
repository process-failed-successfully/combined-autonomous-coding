import argparse
import base64
import sys

def run_base64url_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = base64.urlsafe_b64encode(text).decode('utf-8').rstrip('=')
            print(encoded)
        elif getattr(args, "decode", None):
            # Add padding back if necessary
            padding_needed = len(args.decode) % 4
            padded_string = args.decode + ('=' * ((4 - padding_needed) % 4))
            decoded = base64.urlsafe_b64decode(padded_string).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base64url: {e}", file=sys.stderr)
        return False
