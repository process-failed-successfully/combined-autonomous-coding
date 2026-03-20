import argparse
import sys


BASE45_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
DECODE_TABLE = {char: idx for idx, char in enumerate(BASE45_ALPHABET)}


def b45encode(b: bytes) -> str:
    """Encode bytes to a Base45 string."""
    if not b:
        return ""

    res = []
    for i in range(0, len(b), 2):
        if len(b) - i > 1:
            val = (b[i] << 8) + b[i + 1]
            e, rest = divmod(val, 45 * 45)
            d, c = divmod(rest, 45)
            res.extend([BASE45_ALPHABET[c], BASE45_ALPHABET[d], BASE45_ALPHABET[e]])
        else:
            val = b[i]
            d, c = divmod(val, 45)
            res.extend([BASE45_ALPHABET[c], BASE45_ALPHABET[d]])

    return "".join(res)


def b45decode(s: str) -> bytes:
    """Decode a Base45 string to bytes."""
    if not s:
        return b""

    for char in s:
        if char not in DECODE_TABLE:
            raise ValueError(f"Invalid Base45 character: {char}")

    res = []
    for i in range(0, len(s), 3):
        if len(s) - i >= 3:
            c = DECODE_TABLE[s[i]]
            d = DECODE_TABLE[s[i + 1]]
            e = DECODE_TABLE[s[i + 2]]
            val = c + d * 45 + e * 45 * 45
            if val > 0xFFFF:
                raise ValueError("Invalid Base45 sequence")
            res.extend([val >> 8, val & 0xFF])
        elif len(s) - i == 2:
            c = DECODE_TABLE[s[i]]
            d = DECODE_TABLE[s[i + 1]]
            val = c + d * 45
            if val > 0xFF:
                raise ValueError("Invalid Base45 sequence")
            res.append(val)
        else:
            raise ValueError("Invalid Base45 string length")

    return bytes(res)


def run_base45_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = b45encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = b45decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base45: {e}", file=sys.stderr)
        return False
