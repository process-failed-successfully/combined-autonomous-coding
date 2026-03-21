import argparse
import sys
import idna


def run_punycode_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode
            # Encode each label in the domain
            encoded = idna.encode(text).decode('utf-8')
            print(encoded)
        elif getattr(args, "decode", None):
            text = args.decode
            # Decode each label in the domain
            decoded = idna.decode(text)
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing punycode: {e}", file=sys.stderr)
        return False
