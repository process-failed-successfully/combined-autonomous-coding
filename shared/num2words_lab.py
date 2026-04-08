"""
Number to Words Lab
===================

Utilities for converting numbers to their English word representation.
"""

import sys

class Num2WordsManager:
    """Manages conversion of integers to English words."""

    ONES = [
        "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen"
    ]

    TENS = [
        "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
    ]

    SCALES = [
        "", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion"
    ]

    def convert(self, number: int) -> str:
        """Converts an integer to English words."""
        if not isinstance(number, int):
            try:
                number = int(number)
            except ValueError:
                raise ValueError("Input must be a valid integer.")

        if number == 0:
            return "zero"

        is_negative = number < 0
        if is_negative:
            number = abs(number)

        if number >= 10 ** (3 * len(self.SCALES)):
            raise ValueError("Number too large")

        chunks = []
        while number > 0:
            chunks.append(number % 1000)
            number //= 1000

        words = []
        for i, chunk in enumerate(chunks):
            if chunk == 0:
                continue

            chunk_words = []
            hundreds = chunk // 100
            remainder = chunk % 100

            if hundreds > 0:
                chunk_words.append(f"{self.ONES[hundreds]} hundred")

            if remainder > 0:
                if remainder < 20:
                    chunk_words.append(self.ONES[remainder])
                else:
                    tens = remainder // 10
                    ones = remainder % 10
                    tens_str = self.TENS[tens]
                    if ones > 0:
                        chunk_words.append(f"{tens_str}-{self.ONES[ones]}")
                    else:
                        chunk_words.append(tens_str)

            if i > 0:
                chunk_words.append(self.SCALES[i])

            words.append(" ".join(chunk_words))

        result = " ".join(reversed(words))
        if is_negative:
            result = f"negative {result}"

        return result


def run_num2words_lab_logic(args) -> bool:
    """CLI handler for Num2Words Lab."""

    if getattr(args, "tui", False):
        from main import run_tui
        print("Launching Num2Words Lab TUI...")
        run_tui(args, start_tab="tab-num2words-lab")
        return True

    manager = Num2WordsManager()

    number_str = getattr(args, "number", None)
    if not number_str:
        if not sys.stdin.isatty():
            number_str = sys.stdin.read().strip()

        if not number_str:
            print("Error: Number is required for conversion.")
            return False

    try:
        words = manager.convert(number_str)
        print(words)
        return True
    except ValueError as e:
        print(f"Error: {e}")
        return False
