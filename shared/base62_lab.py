import argparse
import sys

BASE62_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def b62encode(b: bytes) -> str:
    """Encode bytes to a Base62 string."""
    if not b:
        return ""

    n = int.from_bytes(b, 'big')
    chars = []
    while n > 0:
        n, r = divmod(n, 62)
        chars.append(BASE62_ALPHABET[r])

    # Pad with leading zeros
    for byte in b:
        if byte == 0:
            chars.append(BASE62_ALPHABET[0])
        else:
            break

    return ''.join(reversed(chars)) if chars else BASE62_ALPHABET[0]


def b62decode(s: str) -> bytes:
    """Decode a Base62 string to bytes."""
    if not s:
        return b""

    n = 0
    for c in s:
        n *= 62
        if c not in BASE62_ALPHABET:
            raise ValueError(f"Invalid character {c!r} in Base62 string")
        n += BASE62_ALPHABET.index(c)

    b = n.to_bytes((n.bit_length() + 7) // 8, 'big') if n > 0 else b""

    # Pad with leading zeros
    zeros = 0
    for c in s:
        if c == BASE62_ALPHABET[0]:
            zeros += 1
        else:
            break

    return b"\x00" * zeros + b


def run_base62_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = b62encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = b62decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base62: {e}", file=sys.stderr)
        return False
