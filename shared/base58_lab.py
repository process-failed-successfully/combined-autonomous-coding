import argparse
import sys

BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58encode(b: bytes) -> str:
    """Encode bytes to a Base58 string."""
    if not b:
        return ""

    n = int.from_bytes(b, 'big')
    chars = []
    while n > 0:
        n, r = divmod(n, 58)
        chars.append(BASE58_ALPHABET[r])

    # Pad with leading zeros
    for byte in b:
        if byte == 0:
            chars.append(BASE58_ALPHABET[0])
        else:
            break

    return ''.join(reversed(chars))


def b58decode(s: str) -> bytes:
    """Decode a Base58 string to bytes."""
    if not s:
        return b""

    n = 0
    for c in s:
        n *= 58
        if c not in BASE58_ALPHABET:
            raise ValueError(f"Invalid character {c!r} in Base58 string")
        n += BASE58_ALPHABET.index(c)

    b = n.to_bytes((n.bit_length() + 7) // 8, 'big') if n > 0 else b""

    # Pad with leading zeros
    zeros = 0
    for c in s:
        if c == BASE58_ALPHABET[0]:
            zeros += 1
        else:
            break

    return b"\x00" * zeros + b


def run_base58_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = b58encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = b58decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base58: {e}", file=sys.stderr)
        return False
