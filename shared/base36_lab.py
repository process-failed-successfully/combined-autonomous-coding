import argparse
import sys

BASE36_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

def base36_encode(data: bytes) -> str:
    """Encodes bytes to a base36 string."""
    if not data:
        return ""

    num = int.from_bytes(data, byteorder="big")

    if num == 0:
        return "0" * len(data)

    chars = []
    while num > 0:
        num, rem = divmod(num, 36)
        chars.append(BASE36_ALPHABET[rem])

    # Handle leading zero bytes
    for byte in data:
        if byte == 0:
            chars.append("0")
        else:
            break

    return "".join(reversed(chars))

def base36_decode(data: str) -> bytes:
    """Decodes a base36 string to bytes."""
    if not data:
        return b""

    data = data.lower()

    num = 0
    for char in data:
        if char not in BASE36_ALPHABET:
            raise ValueError(f"Invalid character in base36 string: '{char}'")
        num = num * 36 + BASE36_ALPHABET.index(char)

    # Count leading zeros to pad
    leading_zeros = 0
    for char in data:
        if char == "0":
            leading_zeros += 1
        else:
            break

    res = []
    while num > 0:
        res.append(num & 0xFF)
        num >>= 8

    res = bytes(reversed(res))
    return (b"\x00" * leading_zeros) + res

def run_base36_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = base36_encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = base36_decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base36: {e}", file=sys.stderr)
        return False
