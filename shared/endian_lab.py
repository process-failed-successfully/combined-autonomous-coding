import argparse
import sys
import struct

class EndianManager:
    @staticmethod
    def convert_hex(hex_str: str) -> str:
        """Swaps endianness of a hex string."""
        # Remove common prefixes/suffixes
        hex_str = hex_str.replace("0x", "").replace(" ", "").replace(",", "").replace("-", "")

        # Ensure even length
        if len(hex_str) % 2 != 0:
            raise ValueError("Hex string must have an even number of characters.")

        # Split into bytes
        bytes_list = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]

        # Reverse bytes
        reversed_bytes = bytes_list[::-1]

        return "".join(reversed_bytes)

    @staticmethod
    def convert_int(number: int, size: int) -> int:
        """Swaps endianness of an integer of given byte size."""
        if size not in [2, 4, 8]:
            raise ValueError("Size must be 2, 4, or 8 bytes for integer conversion.")

        if size == 2:
            fmt = 'H'
        elif size == 4:
            fmt = 'I'
        elif size == 8:
            fmt = 'Q'

        # Pack as little endian, unpack as big endian
        packed = struct.pack(f"<{fmt}", number)
        unpacked = struct.unpack(f">{fmt}", packed)[0]
        return unpacked


def run_endian_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Endian Lab."""
    manager = EndianManager()

    try:
        if getattr(args, "action", None) == "hex":
            if not getattr(args, "value", None):
                print("Error: Hex string value required.", file=sys.stderr)
                return False
            result = manager.convert_hex(args.value)
            print(result)
            return True

        elif getattr(args, "action", None) == "int":
            if not getattr(args, "value", None) or not getattr(args, "size", None):
                print("Error: Both integer value and size required.", file=sys.stderr)
                return False

            try:
                val = int(args.value)
                size = int(args.size)
            except ValueError:
                print("Error: Value and size must be integers.", file=sys.stderr)
                return False

            result = manager.convert_int(val, size)
            print(result)
            return True

        else:
            print("Error: Action must be 'hex' or 'int'.", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
