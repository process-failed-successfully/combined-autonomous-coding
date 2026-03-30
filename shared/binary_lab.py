import argparse
import sys


def text_to_binary(text: str) -> str:
    """Encodes a string to a space-separated binary representation."""
    if not text:
        return ""
    return " ".join(f"{byte:08b}" for byte in text.encode("utf-8"))


def binary_to_text(binary_str: str) -> str:
    """Decodes a space-separated binary representation back to a string."""
    binary_str = binary_str.strip()
    if not binary_str:
        return ""

    # Remove any extra spaces and split by whitespace
    parts = binary_str.split()
    bytes_list = []

    for part in parts:
        if not all(c in '01' for c in part):
            raise ValueError(f"Invalid binary sequence: {part}")
        bytes_list.append(int(part, 2))

    return bytes(bytes_list).decode("utf-8")


def run_binary_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            encoded = text_to_binary(args.encode)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = binary_to_text(args.decode)
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing binary: {e}", file=sys.stderr)
        return False
