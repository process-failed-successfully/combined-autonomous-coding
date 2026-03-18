import argparse
import sys

# Base91 alphabet and decoding table
BASE91_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+,./:;<=>?@[]^_`{|}~\""
DECODE_TABLE = {char: idx for idx, char in enumerate(BASE91_ALPHABET)}


def base91_encode(data: bytes) -> str:
    """Encodes bytes to a Base91 string."""
    if not data:
        return ""

    encoded = []
    b = 0
    n = 0
    for byte in data:
        b |= byte << n
        n += 8
        if n > 13:
            v = b & 8191
            if v > 88:
                b >>= 13
                n -= 13
            else:
                v = b & 16383
                b >>= 14
                n -= 14
            encoded.append(BASE91_ALPHABET[v % 91])
            encoded.append(BASE91_ALPHABET[v // 91])

    if n > 0:
        encoded.append(BASE91_ALPHABET[b % 91])
        if n > 7 or b > 90:
            encoded.append(BASE91_ALPHABET[b // 91])

    return "".join(encoded)


def base91_decode(data: str) -> bytes:
    """Decodes a Base91 string to bytes."""
    if not data:
        return b""

    decoded = []
    b = 0
    n = 0
    v = -1

    for char in data:
        if char not in DECODE_TABLE:
            continue

        c = DECODE_TABLE[char]
        if v < 0:
            v = c
        else:
            v += c * 91
            b |= v << n
            n += 13 if (v & 8191) > 88 else 14

            while n > 7:
                decoded.append(b & 255)
                b >>= 8
                n -= 8

            v = -1

    if v + 1 > 0:
        decoded.append((b | v << n) & 255)

    return bytes(decoded)


def run_base91_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = base91_encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = base91_decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base91: {e}", file=sys.stderr)
        return False
