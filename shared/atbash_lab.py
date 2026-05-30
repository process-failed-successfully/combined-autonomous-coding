import sys
import argparse


def atbash_cipher(text: str) -> str:
    """Applies an Atbash cipher to the input text."""
    if not text:
        return text

    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr(ord('z') - (ord(char) - ord('a'))))
        elif 'A' <= char <= 'Z':
            result.append(chr(ord('Z') - (ord(char) - ord('A'))))
        else:
            result.append(char)

    return "".join(result)


def run_atbash_lab_logic(args: argparse.Namespace) -> bool:
    """Runs the Atbash Lab logic."""
    text = getattr(args, "text", None)

    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("Error: No input text provided. Provide text as a positional argument or pipe data via stdin.", file=sys.stderr)
            return False

    if not text:
        return False

    result = atbash_cipher(text)
    print(result, end="")
    return True
