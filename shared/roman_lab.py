"""
Roman Numeral Lab
=================

Utilities for converting between integers and Roman numerals.
"""

from typing import Tuple


class RomanLabManager:
    """Manages Roman numeral conversions."""

    ROMAN_NUMERALS = (
        ('M',  1000),
        ('CM', 900),
        ('D',  500),
        ('CD', 400),
        ('C',  100),
        ('XC', 90),
        ('L',  50),
        ('XL', 40),
        ('X',  10),
        ('IX', 9),
        ('V',  5),
        ('IV', 4),
        ('I',  1)
    )

    def int_to_roman(self, n: int) -> str:
        """Converts an integer to a Roman numeral."""
        if not isinstance(n, int):
            raise TypeError("Input must be an integer")
        if not 0 < n < 4000:
            raise ValueError("Integer must be between 1 and 3999")

        result = ""
        for numeral, value in self.ROMAN_NUMERALS:
            while n >= value:
                result += numeral
                n -= value
        return result

    def roman_to_int(self, s: str) -> int:
        """Converts a Roman numeral to an integer."""
        if not isinstance(s, str):
            raise TypeError("Input must be a string")
        if not s:
            raise ValueError("Input cannot be empty")

        s = s.upper().strip()
        result = 0
        i = 0

        while i < len(s):
            # Check for two-character numerals
            if i + 1 < len(s):
                pair = s[i:i+2]
                value = next((val for num, val in self.ROMAN_NUMERALS if num == pair), None)
                if value is not None:
                    result += value
                    i += 2
                    continue

            # Check for single-character numerals
            char = s[i]
            value = next((val for num, val in self.ROMAN_NUMERALS if num == char), None)
            if value is not None:
                result += value
                i += 1
            else:
                raise ValueError(f"Invalid Roman numeral character: {char}")

        # Validate that the resulting integer converts back to the exact same string
        # This catches invalid combinations like 'IIII' or 'IC'
        if self.int_to_roman(result) != s:
            raise ValueError(f"Invalid Roman numeral format: {s}")

        return result

    def convert(self, value: str) -> Tuple[bool, str]:
        """
        Auto-detects and converts the value.
        Returns a tuple of (success, output).
        """
        value = value.strip()

        # Try converting from int to roman
        try:
            int_val = int(value)
            return True, self.int_to_roman(int_val)
        except ValueError:
            pass

        # Try converting from roman to int
        try:
            return True, str(self.roman_to_int(value))
        except ValueError as e:
            return False, str(e)


def run_roman_lab_logic(args) -> bool:
    """CLI handler for Roman Lab."""
    manager = RomanLabManager()

    action = getattr(args, "action", None)

    if action == "convert":
        value = getattr(args, "value", None)
        if not value:
            import sys
            # Check if stdin has data
            if not sys.stdin.isatty():
                value = sys.stdin.read().strip()

            if not value:
                print("Error: Value is required for conversion.")
                return False

        success, output = manager.convert(value)
        if success:
            print(output)
            return True
        else:
            print(f"Error: {output}")
            return False

    print(f"Error: Unknown action '{action}'")
    return False
