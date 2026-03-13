import argparse
import sys

# Base58 alphabet (Bitcoin style)
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58encode(v: bytes) -> str:
    """Encode bytes to a base58-encoded string."""
    if not isinstance(v, bytes):
        raise TypeError("a bytes-like object is required, not '%s'" % type(v).__name__)

    nPad = len(v)
    v = v.lstrip(b'\0')
    nPad -= len(v)

    p, acc = 1, 0
    for c in reversed(v):
        acc += p * c
        p = p << 8

    result = ''
    while acc > 0:
        acc, mod = divmod(acc, 58)
        result += ALPHABET[mod]

    return (ALPHABET[0] * nPad) + result[::-1]

def b58decode(v: str) -> bytes:
    """Decode a base58-encoding string, returning bytes."""
    if not isinstance(v, str):
        v = v.decode('ascii')

    nPad = len(v)
    v = v.lstrip(ALPHABET[0])
    nPad -= len(v)

    acc = 0
    p = 1
    for c in reversed(v):
        try:
            val = ALPHABET.index(c)
        except ValueError:
            raise ValueError(f"Invalid character '{c}' in base58 string")
        acc += val * p
        p *= 58

    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)

    return (b'\0' * nPad) + bytes(reversed(result))

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
