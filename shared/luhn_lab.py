import sys

import random


class LuhnManager:
    """
    Manages validation and generation of numbers using the Luhn algorithm.
    Useful for credit cards, IMEI numbers, and national provider identifiers.
    """

    def validate(self, number: str) -> bool:
        """
        Validates a given number string using the Luhn algorithm.
        Strips non-digit characters before validating.
        """
        # Strip all non-digit characters
        digits = [int(d) for d in str(number) if d.isdigit()]
        if not digits:
            return False

        # Luhn algorithm: double every second digit from right to left
        checksum = 0
        is_second = False

        for digit in reversed(digits):
            if is_second:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
            is_second = not is_second

        return checksum % 10 == 0

    def generate(self, length: int, prefix: str = "") -> str:
        """
        Generates a valid Luhn number of the specified total length.
        An optional prefix can be provided.
        """
        prefix_digits = ''.join(filter(str.isdigit, prefix))

        if length <= len(prefix_digits):
            raise ValueError("Target length must be greater than the prefix length.")

        # Calculate how many random digits we need (excluding the check digit)
        random_length = length - len(prefix_digits) - 1

        # Generate random middle digits
        random_digits = ''.join(str(random.randint(0, 9)) for _ in range(random_length))  # nosec B311

        partial_number = prefix_digits + random_digits

        # Calculate the check digit
        partial_digits = [int(d) for d in partial_number]

        checksum = 0
        is_second = True  # Starting from the rightmost digit of the *partial* number, which will be the second digit of the *final* number

        for digit in reversed(partial_digits):
            if is_second:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
            is_second = not is_second

        check_digit = (10 - (checksum % 10)) % 10

        return partial_number + str(check_digit)


def run_luhn_lab_logic(args):
    """
    CLI logic for the Luhn Lab.
    """
    manager = LuhnManager()

    if args.action == "validate":
        is_valid = manager.validate(args.number)
        if is_valid:
            print(f"✅ The number '{args.number}' is a valid Luhn sequence.")
            sys.exit(0)
        else:
            print(f"❌ The number '{args.number}' is INVALID.")
            sys.exit(1)

    elif args.action == "generate":
        try:
            generated = manager.generate(length=args.length, prefix=args.prefix)
            print(f"✅ Generated valid Luhn sequence: {generated}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
