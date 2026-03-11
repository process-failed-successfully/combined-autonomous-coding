from typing import Any
import sys
import random

class IsbnManager:
    """
    Manages validation, generation, parsing, and conversion of International Standard Book Numbers (ISBN-10 and ISBN-13).
    """

    def validate(self, isbn: str) -> bool:
        """
        Validates a given ISBN string (ISBN-10 or ISBN-13).
        Strips hyphens and spaces before validating.
        """
        isbn = str(isbn).replace("-", "").replace(" ", "").upper()

        if len(isbn) == 10:
            return self._validate_isbn10(isbn)
        elif len(isbn) == 13:
            return self._validate_isbn13(isbn)
        else:
            return False

    def _validate_isbn10(self, isbn: str) -> bool:
        if not isbn[:-1].isdigit():
            return False
        if isbn[-1] not in "0123456789X":
            return False

        checksum = 0
        for i in range(9):
            checksum += int(isbn[i]) * (10 - i)

        last_char = 10 if isbn[-1] == 'X' else int(isbn[-1])
        checksum += last_char

        return checksum % 11 == 0

    def _validate_isbn13(self, isbn: str) -> bool:
        if not isbn.isdigit():
            return False

        checksum = 0
        for i in range(12):
            multiplier = 1 if i % 2 == 0 else 3
            checksum += int(isbn[i]) * multiplier

        check_digit = (10 - (checksum % 10)) % 10
        return check_digit == int(isbn[-1])

    def generate(self, format_type: str = "13", prefix: str = "978") -> str:
        """
        Generates a valid random ISBN-10 or ISBN-13.
        """
        if format_type == "10":
            # Generate 9 random digits
            digits = "".join(str(random.randint(0, 9)) for _ in range(9))  # nosec B311

            checksum = 0
            for i in range(9):
                checksum += int(digits[i]) * (10 - i)

            remainder = checksum % 11
            check_digit = (11 - remainder) % 11

            check_char = 'X' if check_digit == 10 else str(check_digit)
            return digits + check_char

        elif format_type == "13":
            if prefix not in ["978", "979"]:
                raise ValueError("ISBN-13 prefix must be 978 or 979.")

            # Generate 9 random digits after prefix
            digits = prefix + "".join(str(random.randint(0, 9)) for _ in range(9))  # nosec B311

            checksum = 0
            for i in range(12):
                multiplier = 1 if i % 2 == 0 else 3
                checksum += int(digits[i]) * multiplier

            check_digit = (10 - (checksum % 10)) % 10
            return digits + str(check_digit)
        else:
            raise ValueError("Format type must be '10' or '13'.")

    def parse(self, isbn: str) -> dict[str, Any]:
        """
        Parses an ISBN into its components and validates it.
        (Note: Accurate splitting into group/publisher/title requires a massive database.
        This provides a simplified logical split based on fixed length approximations for lab purposes.)
        """
        original_isbn = str(isbn).strip()
        clean_isbn = original_isbn.replace("-", "").replace(" ", "").upper()

        is_valid = self.validate(clean_isbn)

        if len(clean_isbn) == 10:
            return {
                "isbn": original_isbn,
                "clean_isbn": clean_isbn,
                "format": "ISBN-10",
                "registration_group": clean_isbn[0:2],  # Approximation
                "registrant": clean_isbn[2:6],          # Approximation
                "publication": clean_isbn[6:9],         # Approximation
                "checksum": clean_isbn[9],
                "is_valid": is_valid
            }
        elif len(clean_isbn) == 13:
            return {
                "isbn": original_isbn,
                "clean_isbn": clean_isbn,
                "format": "ISBN-13",
                "prefix": clean_isbn[0:3],
                "registration_group": clean_isbn[3:5],  # Approximation
                "registrant": clean_isbn[5:9],          # Approximation
                "publication": clean_isbn[9:12],        # Approximation
                "checksum": clean_isbn[12],
                "is_valid": is_valid
            }
        else:
            raise ValueError("Invalid ISBN length. Must be 10 or 13 digits.")

    def convert(self, isbn10: str) -> str:
        """
        Converts a valid ISBN-10 to an ISBN-13.
        """
        clean_isbn10 = str(isbn10).replace("-", "").replace(" ", "").upper()

        if len(clean_isbn10) != 10 or not self.validate(clean_isbn10):
            raise ValueError("Invalid ISBN-10 provided for conversion.")

        # Drop the check digit of ISBN-10 and prepend 978
        base_digits = "978" + clean_isbn10[:-1]

        checksum = 0
        for i in range(12):
            multiplier = 1 if i % 2 == 0 else 3
            checksum += int(base_digits[i]) * multiplier

        check_digit = (10 - (checksum % 10)) % 10
        return base_digits + str(check_digit)

def run_isbn_lab_logic(args):
    """
    CLI logic for the ISBN Lab.
    """
    manager = IsbnManager()

    if args.action == "validate":
        is_valid = manager.validate(args.isbn)
        if is_valid:
            print(f"✅ The ISBN '{args.isbn}' is valid.")
            sys.exit(0)
        else:
            print(f"❌ The ISBN '{args.isbn}' is INVALID.")
            sys.exit(1)

    elif args.action == "generate":
        try:
            format_type = getattr(args, 'format', '13')
            prefix = getattr(args, 'prefix', '978')
            generated = manager.generate(format_type=format_type, prefix=prefix)
            print(f"✅ Generated valid ISBN-{format_type}: {generated}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "parse":
        try:
            parsed = manager.parse(args.isbn)
            print(f"Original ISBN: {parsed['isbn']}")
            print(f"Clean ISBN: {parsed['clean_isbn']}")
            print(f"Format: {parsed['format']}")
            if 'prefix' in parsed:
                print(f"Prefix: {parsed['prefix']}")
            print(f"Registration Group: {parsed['registration_group']}")
            print(f"Registrant: {parsed['registrant']}")
            print(f"Publication: {parsed['publication']}")
            print(f"Checksum: {parsed['checksum']}")
            print(f"Valid: {'Yes' if parsed['is_valid'] else 'No'}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "convert":
        try:
            converted = manager.convert(args.isbn)
            print(f"✅ Converted ISBN-10 '{args.isbn}' to ISBN-13: {converted}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
