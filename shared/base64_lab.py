import argparse
import base64
import sys

def run_base64_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if args.encode:
            text = args.encode.encode('utf-8')
            encoded = base64.b64encode(text).decode('utf-8')
            print(encoded)
        elif args.decode:
            decoded = base64.b64decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode or --decode", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base64: {e}", file=sys.stderr)
        return False
