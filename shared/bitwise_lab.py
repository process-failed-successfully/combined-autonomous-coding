import sys
from typing import Dict


class BitwiseLabManager:
    """Manages Bitwise Lab operations: conversions, logical ops, and byte swapping."""

    def __init__(self):
        pass

    def parse_value(self, value_str: str) -> int:
        """Parses a string into an integer (supports hex, binary, octal, decimal)."""
        value_str = str(value_str).strip()
        if not value_str:
            return 0
        try:
            if value_str.startswith(("0x", "0X")):
                return int(value_str, 16)
            elif value_str.startswith(("0b", "0B")):
                return int(value_str, 2)
            elif value_str.startswith(("0o", "0O")):
                return int(value_str, 8)
            else:
                return int(value_str, 10)
        except ValueError:
            raise ValueError(f"Invalid integer format: {value_str}")

    def format_value(self, value: int, bits: int = 32) -> Dict[str, str]:
        """Formats an integer into decimal, hex, binary, and octal strings."""
        # Ensure it fits within the specified bits (unsigned representation)
        mask = (1 << bits) - 1
        masked_val = value & mask

        # Calculate signed representation
        signed_val = masked_val
        if signed_val & (1 << (bits - 1)):
            signed_val -= (1 << bits)

        return {
            "dec_unsigned": str(masked_val),
            "dec_signed": str(signed_val),
            "hex": f"0x{masked_val:0{bits // 4}X}",
            "bin": f"0b{masked_val:0{bits}b}",
            "oct": f"0o{masked_val:o}"
        }

    def bitwise_and(self, val1: int, val2: int, bits: int = 32) -> int:
        mask = (1 << bits) - 1
        return (val1 & val2) & mask

    def bitwise_or(self, val1: int, val2: int, bits: int = 32) -> int:
        mask = (1 << bits) - 1
        return (val1 | val2) & mask

    def bitwise_xor(self, val1: int, val2: int, bits: int = 32) -> int:
        mask = (1 << bits) - 1
        return (val1 ^ val2) & mask

    def bitwise_not(self, val1: int, bits: int = 32) -> int:
        mask = (1 << bits) - 1
        return (~val1) & mask

    def bitwise_lshift(self, val1: int, shift: int, bits: int = 32) -> int:
        mask = (1 << bits) - 1
        return (val1 << shift) & mask

    def bitwise_rshift(self, val1: int, shift: int, bits: int = 32) -> int:
        # Logical right shift (unsigned)
        mask = (1 << bits) - 1
        val1 &= mask
        return (val1 >> shift) & mask

    def swap_bytes(self, value: int, bits: int = 32) -> int:
        """Swaps the endianness of the value (16, 32, or 64 bits)."""
        if bits not in [16, 32, 64]:
            raise ValueError("Byte swapping only supported for 16, 32, or 64 bits.")

        mask = (1 << bits) - 1
        value &= mask

        bytes_val = value.to_bytes(bits // 8, byteorder='little')
        return int.from_bytes(bytes_val, byteorder='big')


def run_bitwise_lab_logic(args) -> bool:
    """CLI handler for Bitwise Lab."""
    manager = BitwiseLabManager()

    try:
        bits = getattr(args, "bits", 32)
        val1 = manager.parse_value(args.val1)
        val2 = manager.parse_value(getattr(args, "val2", "0")) if hasattr(args, "val2") and args.val2 else 0

        action = args.action

        if action == "format":
            result = val1
        elif action == "and":
            result = manager.bitwise_and(val1, val2, bits)
        elif action == "or":
            result = manager.bitwise_or(val1, val2, bits)
        elif action == "xor":
            result = manager.bitwise_xor(val1, val2, bits)
        elif action == "not":
            result = manager.bitwise_not(val1, bits)
        elif action == "lshift":
            result = manager.bitwise_lshift(val1, val2, bits)
        elif action == "rshift":
            result = manager.bitwise_rshift(val1, val2, bits)
        elif action == "swap":
            result = manager.swap_bytes(val1, bits)
        else:
            print(f"Error: Unknown action '{action}'.", file=sys.stderr)
            return False

        formatted = manager.format_value(result, bits)

        if getattr(args, "json", False):
            import json
            print(json.dumps(formatted, indent=2))
        else:
            print(f"Result (Unsigned): {formatted['dec_unsigned']}")
            print(f"Result (Signed):   {formatted['dec_signed']}")
            print(f"Hex:               {formatted['hex']}")
            print(f"Binary:            {formatted['bin']}")
            print(f"Octal:             {formatted['oct']}")

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
