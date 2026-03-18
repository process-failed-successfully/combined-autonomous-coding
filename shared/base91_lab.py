"""
Base91 Encoding/Decoding Lab.
"""
import argparse
import sys


base91_alphabet = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$',
    '%', '&', '(', ')', '*', '+', ',', '.', '/', ':', ';', '<', '=',
    '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~', '"'
]

decode_table = {v: k for k, v in enumerate(base91_alphabet)}


def base91_encode(bindata: bytes) -> str:
    """Encode a byte array to a Base91 string."""
    b = 0
    n = 0
    out = ''
    for byte in bindata:
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
            out += base91_alphabet[v % 91] + base91_alphabet[v // 91]
    if n:
        out += base91_alphabet[b % 91]
        if n > 7 or b > 90:
            out += base91_alphabet[b // 91]
    return out


def base91_decode(ascdata: str) -> bytes:
    """Decode a Base91 string to a byte array."""
    b = 0
    n = 0
    v = -1
    out = bytearray()
    for char in ascdata:
        if char not in decode_table:
            continue
        c = decode_table[char]
        if v < 0:
            v = c
        else:
            v += c * 91
            b |= v << n
            n += 13 if (v & 8191) > 88 else 14
            while True:
                out.append(b & 255)
                b >>= 8
                n -= 8
                if not n > 7:
                    break
            v = -1
    if v + 1:
        out.append((b | v << n) & 255)
    return bytes(out)


def run_base91_lab_logic(args: argparse.Namespace) -> bool:
    """Core logic for base91 encoding and decoding."""
    try:
        if getattr(args, 'encode', None) is not None:
            text = args.encode.encode('utf-8')
            encoded = base91_encode(text)
            print(encoded)
            return True
        elif getattr(args, 'decode', None) is not None:
            decoded = base91_decode(args.decode).decode('utf-8')
            print(decoded)
            return True
        else:
            print("No action specified. Use --encode or --decode.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error processing base91: {e}", file=sys.stderr)
        return False
