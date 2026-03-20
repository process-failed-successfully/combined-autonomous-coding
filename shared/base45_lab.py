import argparse
import sys


# Base45 Alphabet defined in RFC 9285
BASE45_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
BASE45_DECODE_MAP = {char: idx for idx, char in enumerate(BASE45_ALPHABET)}


def base45_encode(data: bytes) -> str:
    """
    Encodes a byte string to a Base45 string according to RFC 9285.
    """
    res = []

    # Process pairs of bytes
    for i in range(0, len(data) - len(data) % 2, 2):
        val = (data[i] << 8) + data[i+1]
        e, rest = divmod(val, 45 * 45)
        d, c = divmod(rest, 45)
        res.append(BASE45_ALPHABET[c])
        res.append(BASE45_ALPHABET[d])
        res.append(BASE45_ALPHABET[e])

    # Process remaining byte if any
    if len(data) % 2 == 1:
        val = data[-1]
        d, c = divmod(val, 45)
        res.append(BASE45_ALPHABET[c])
        res.append(BASE45_ALPHABET[d])

    return "".join(res)


def base45_decode(encoded_str: str) -> bytes:
    """
    Decodes a Base45 string to a byte string according to RFC 9285.
    """
    res = []

    if len(encoded_str) % 3 == 1:
        raise ValueError("Invalid Base45 string length")

    try:
        # Process triplets of characters
        for i in range(0, len(encoded_str) - len(encoded_str) % 3, 3):
            c = BASE45_DECODE_MAP[encoded_str[i]]
            d = BASE45_DECODE_MAP[encoded_str[i+1]]
            e = BASE45_DECODE_MAP[encoded_str[i+2]]

            val = c + 45 * d + 45 * 45 * e

            if val > 65535:
                raise ValueError("Invalid Base45 value")

            res.append(val >> 8)
            res.append(val & 255)

        # Process remaining pair of characters if any
        if len(encoded_str) % 3 == 2:
            c = BASE45_DECODE_MAP[encoded_str[-2]]
            d = BASE45_DECODE_MAP[encoded_str[-1]]

            val = c + 45 * d

            if val > 255:
                raise ValueError("Invalid Base45 value")

            res.append(val)

    except KeyError as e:
        raise ValueError(f"Invalid character in Base45 string: {e}")

    return bytes(res)


def run_base45_lab_logic(args: argparse.Namespace) -> bool:
    """
    CLI logic for the base45-lab command.
    """
    try:
        if getattr(args, "encode", None):
            text = args.encode.encode('utf-8')
            encoded = base45_encode(text)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded_bytes = base45_decode(args.decode)
            # Try to decode as utf-8, but might be raw bytes in some contexts
            try:
                print(decoded_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                print(decoded_bytes)  # fallback to bytes representation
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing base45: {e}", file=sys.stderr)
        return False
