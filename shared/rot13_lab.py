import sys
import codecs
from typing import Optional

def run_rot13_lab_logic(args) -> bool:
    """CLI handler for ROT13 Lab."""

    def get_input(arg_val: Optional[str]) -> Optional[str]:
        if arg_val:
            return arg_val
        # Try stdin
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read().strip()
            except Exception:
                pass
        return None

    text_input = get_input(args.text)
    if not text_input:
        print("Error: Input text required (argument or stdin).", file=sys.stderr)
        return False

    try:
        encoded_text = codecs.encode(text_input, 'rot_13')
        print(encoded_text)
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
