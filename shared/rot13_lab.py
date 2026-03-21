import sys
from codecs import encode

def run_rot13_lab_logic(args) -> bool:
    """Runs the ROT13 Lab logic."""
    text = getattr(args, "text", None)

    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("Error: No input text provided. Provide text as a positional argument or pipe data via stdin.", file=sys.stderr)
            return False

    if not text:
        return False

    result = encode(text, "rot_13")
    print(result, end="")
    return True
