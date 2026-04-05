import argparse
import sys

def base92_encode(data: bytes) -> str:
    """Encodes bytes to a Base92 string."""
    if not data:
        return "~"

    # Base92 implementation based on standard
    base92_chars = "!#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_abcdefghijklmnopqrstuvwxyz{|}"

    bit_str = ""
    for byte in data:
        bit_str += bin(byte)[2:].zfill(8)

    res = ""
    while len(bit_str) >= 13:
        i = int(bit_str[:13], 2)
        res += base92_chars[i // 91] + base92_chars[i % 91]
        bit_str = bit_str[13:]

    if bit_str:
        if len(bit_str) < 7:
            bit_str += '0' * (6 - len(bit_str))
            i = int(bit_str, 2)
            res += base92_chars[i]
        else:
            bit_str += '0' * (13 - len(bit_str))
            i = int(bit_str, 2)
            res += base92_chars[i // 91] + base92_chars[i % 91]
    return res

def base92_decode(data: str) -> bytes:
    """Decodes a Base92 string to bytes."""
    if data == "~":
        return b""
    if not data:
        return b""

    base92_chars = "!#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_abcdefghijklmnopqrstuvwxyz{|}"
    base92_dict = {c: i for i, c in enumerate(base92_chars)}

    bit_str = ""
    res = bytearray()

    i = 0
    while i < len(data):
        if data[i] == '~':
            # empty case handled
            i += 1
            continue

        if i + 1 < len(data) and data[i+1] != '~':
            try:
                val = base92_dict[data[i]] * 91 + base92_dict[data[i+1]]
            except KeyError:
                raise ValueError("Invalid Base92 character")
            bit_str += bin(val)[2:].zfill(13)
            i += 2
        else:
            try:
                val = base92_dict[data[i]]
            except KeyError:
                raise ValueError("Invalid Base92 character")
            bit_str += bin(val)[2:].zfill(6)
            i += 1

        while len(bit_str) >= 8:
            res.append(int(bit_str[:8], 2))
            bit_str = bit_str[8:]

    return bytes(res)

def run_base92_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "encode", None) is not None:
            text = args.encode.encode('utf-8')
            encoded = base92_encode(text)
            print(encoded)
        elif getattr(args, "decode", None) is not None:
            decoded = base92_decode(args.decode).decode('utf-8')
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base92: {e}", file=sys.stderr)
        return False
