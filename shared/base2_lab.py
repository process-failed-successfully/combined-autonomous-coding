import argparse
import sys


def encode_base2(text: str) -> str:
    """Encodes a utf-8 string into a space-separated binary string."""
    return ' '.join(format(byte, '08b') for byte in text.encode('utf-8'))


def decode_base2(binary_str: str) -> str:
    """Decodes a space-separated or continuous binary string back to a utf-8 string."""
    # Remove all spaces to handle both continuous and space-separated binary strings
    binary_str = binary_str.replace(" ", "")

    if len(binary_str) % 8 != 0:
        raise ValueError("Binary string length must be a multiple of 8.")

    # Process 8 bits at a time
    byte_array = bytearray()
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if not all(bit in '01' for bit in byte):
            raise ValueError(f"Invalid characters in binary string: {byte}")
        byte_array.append(int(byte, 2))

    return byte_array.decode('utf-8')


def run_base2_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for encoding/decoding Base2."""
    try:
        if getattr(args, "encode", None):
            encoded = encode_base2(args.encode)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = decode_base2(args.decode)
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except ValueError as ve:
        print(f"Error: {ve}", file=sys.stderr)
        return False
    except UnicodeDecodeError as ude:
        print(f"Error decoding binary to UTF-8: {ude}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error processing base2: {e}", file=sys.stderr)
        return False
