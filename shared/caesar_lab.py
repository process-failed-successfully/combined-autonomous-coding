import sys
import argparse

def caesar_cipher(text: str, shift: int, decode: bool = False) -> str:
    """Applies a Caesar cipher to the input text."""
    if decode:
        shift = -shift

    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
        else:
            result.append(char)

    return "".join(result)

def run_caesar_lab_logic(args: argparse.Namespace) -> bool:
    """Runs the Caesar Lab logic."""
    text = getattr(args, "text", None)

    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("Error: No input text provided. Provide text as a positional argument or pipe data via stdin.", file=sys.stderr)
            return False

    if not text:
        return False

    shift = getattr(args, "shift", 13)
    decode = getattr(args, "decode", False)

    result = caesar_cipher(text, shift, decode)
    print(result, end="")
    return True
