import sys
import argparse


def vigenere_cipher(text: str, key: str, decode: bool = False) -> str:
    """Applies a Vigenère cipher to the input text."""
    if not key:
        return text

    key_shifts = []
    for k in key:
        if k.isalpha():
            key_shifts.append(ord(k.lower()) - ord('a'))

    if not key_shifts:
        return text

    result = []
    key_idx = 0
    key_len = len(key_shifts)

    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shift = key_shifts[key_idx % key_len]
            if decode:
                shift = -shift

            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
            key_idx += 1
        else:
            result.append(char)

    return "".join(result)


def run_vigenere_lab_logic(args: argparse.Namespace) -> bool:
    """Runs the Vigenère Lab logic."""
    text = getattr(args, "text", None)

    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("Error: No input text provided. Provide text as a positional argument or pipe data via stdin.", file=sys.stderr)
            return False

    if not text:
        return False

    key = getattr(args, "key", "")
    if not key:
        print("Error: Vigenère cipher requires a --key", file=sys.stderr)
        return False

    decode = getattr(args, "decode", False)

    result = vigenere_cipher(text, key, decode)
    print(result, end="")
    return True
