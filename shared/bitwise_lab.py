import sys
from typing import Dict, Union, Any, Tuple

class BitwiseLabManager:
    """Manages bitwise operations and base conversions."""

    def __init__(self) -> None:
        pass

    def parse_number(self, num_str: str) -> int:
        """Parses a string into an integer, supporting hex (0x), binary (0b), octal (0o) prefixes, and base 10."""
        num_str = num_str.strip().lower()
        try:
            if num_str.startswith('0x'):
                return int(num_str, 16)
            elif num_str.startswith('0b'):
                return int(num_str, 2)
            elif num_str.startswith('0o'):
                return int(num_str, 8)
            else:
                return int(num_str)
        except ValueError:
            raise ValueError(f"Could not parse number: {num_str}")

    def format_number(self, number: int) -> Dict[str, str]:
        """Formats a number into decimal, hex, binary, and octal strings."""
        return {
            "dec": str(number),
            "hex": hex(number),
            "bin": bin(number),
            "oct": oct(number)
        }

    def bitwise_and(self, num1_str: str, num2_str: str) -> Dict[str, str]:
        """Performs bitwise AND on two numbers."""
        n1 = self.parse_number(num1_str)
        n2 = self.parse_number(num2_str)
        return self.format_number(n1 & n2)

    def bitwise_or(self, num1_str: str, num2_str: str) -> Dict[str, str]:
        """Performs bitwise OR on two numbers."""
        n1 = self.parse_number(num1_str)
        n2 = self.parse_number(num2_str)
        return self.format_number(n1 | n2)

    def bitwise_xor(self, num1_str: str, num2_str: str) -> Dict[str, str]:
        """Performs bitwise XOR on two numbers."""
        n1 = self.parse_number(num1_str)
        n2 = self.parse_number(num2_str)
        return self.format_number(n1 ^ n2)

    def bitwise_not(self, num_str: str) -> Dict[str, str]:
        """Performs bitwise NOT on a number."""
        n1 = self.parse_number(num_str)
        return self.format_number(~n1)

    def left_shift(self, num_str: str, shift_by_str: str) -> Dict[str, str]:
        """Performs left shift on a number by a specified amount."""
        n1 = self.parse_number(num_str)
        shift_by = self.parse_number(shift_by_str)
        if shift_by < 0:
            raise ValueError("Shift amount must be non-negative.")
        return self.format_number(n1 << shift_by)

    def right_shift(self, num_str: str, shift_by_str: str) -> Dict[str, str]:
        """Performs right shift on a number by a specified amount."""
        n1 = self.parse_number(num_str)
        shift_by = self.parse_number(shift_by_str)
        if shift_by < 0:
            raise ValueError("Shift amount must be non-negative.")
        return self.format_number(n1 >> shift_by)


def run_bitwise_lab_logic(args) -> bool:
    """CLI handler for Bitwise Lab operations."""
    manager = BitwiseLabManager()

    if getattr(args, "action", None) == "tui":
        return True

    action = args.action

    try:
        if action == "convert":
            if not args.num:
                print("Error: Number required for conversion.", file=sys.stderr)
                return False
            res = manager.format_number(manager.parse_number(args.num))
            print(f"Decimal: {res['dec']}")
            print(f"Hex:     {res['hex']}")
            print(f"Binary:  {res['bin']}")
            print(f"Octal:   {res['oct']}")
            return True

        elif action in ["and", "or", "xor", "lshift", "rshift"]:
            if not args.num1 or not args.num2:
                print(f"Error: num1 and num2 required for '{action}' operation.", file=sys.stderr)
                return False

            if action == "and":
                res = manager.bitwise_and(args.num1, args.num2)
            elif action == "or":
                res = manager.bitwise_or(args.num1, args.num2)
            elif action == "xor":
                res = manager.bitwise_xor(args.num1, args.num2)
            elif action == "lshift":
                res = manager.left_shift(args.num1, args.num2)
            elif action == "rshift":
                res = manager.right_shift(args.num1, args.num2)

            print(f"Result (Decimal): {res['dec']}")
            print(f"Result (Hex):     {res['hex']}")
            print(f"Result (Binary):  {res['bin']}")
            print(f"Result (Octal):   {res['oct']}")
            return True

        elif action == "not":
            if not args.num:
                print("Error: Number required for 'not' operation.", file=sys.stderr)
                return False

            res = manager.bitwise_not(args.num)
            print(f"Result (Decimal): {res['dec']}")
            print(f"Result (Hex):     {res['hex']}")
            print(f"Result (Binary):  {res['bin']}")
            print(f"Result (Octal):   {res['oct']}")
            return True

        else:
            print(f"Error: Unknown action '{action}'.", file=sys.stderr)
            return False

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False
