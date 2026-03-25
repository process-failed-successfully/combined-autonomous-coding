import argparse
import sys


def run_octal_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = " ".join(f"{b:03o}" for b in text)
            print(encoded)
        elif getattr(args, "decode", None):
            octal_parts = args.decode.strip().split()
            try:
                decoded_bytes = bytes(int(p, 8) for p in octal_parts)
            except ValueError:
                print("Error: Invalid octal string.", file=sys.stderr)
                return False

            try:
                decoded = decoded_bytes.decode('utf-8')
                print(decoded)
            except UnicodeDecodeError:
                print("Error: Decoded bytes are not valid UTF-8.", file=sys.stderr)
                return False
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing octal: {e}", file=sys.stderr)
        return False
