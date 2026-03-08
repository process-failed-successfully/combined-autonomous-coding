import sys
import string
import random

IBAN_FORMATS = {
    'AL': 28, 'AD': 24, 'AT': 20, 'AZ': 28, 'BH': 22, 'BY': 28, 'BE': 16, 'BA': 20, 'BR': 29,
    'BG': 22, 'CR': 22, 'HR': 21, 'CY': 28, 'CZ': 24, 'DK': 18, 'DO': 28, 'EG': 29, 'SV': 28,
    'EE': 20, 'FO': 18, 'FI': 18, 'FR': 27, 'GE': 22, 'DE': 22, 'GI': 23, 'GR': 27, 'GL': 18,
    'GT': 28, 'VA': 22, 'HU': 28, 'IS': 26, 'IQ': 23, 'IE': 22, 'IL': 23, 'IT': 27, 'JO': 30,
    'KZ': 20, 'XK': 20, 'KW': 30, 'LV': 21, 'LB': 28, 'LI': 21, 'LT': 20, 'LU': 20, 'MT': 31,
    'MR': 27, 'MU': 30, 'MD': 24, 'MC': 27, 'ME': 22, 'NL': 18, 'MK': 19, 'NO': 15, 'PK': 24,
    'PS': 29, 'PL': 28, 'PT': 25, 'QA': 29, 'RO': 24, 'LC': 32, 'SM': 27, 'ST': 25, 'SA': 24,
    'RS': 22, 'SC': 31, 'SK': 24, 'SI': 19, 'ES': 24, 'SD': 18, 'SE': 24, 'CH': 21, 'TL': 23,
    'TN': 24, 'TR': 26, 'UA': 29, 'AE': 23, 'GB': 22, 'VG': 24
}

class IbanManager:
    """
    Manages validation, generation, and parsing of IBANs.
    """

    def validate(self, iban: str) -> bool:
        """
        Validates a given IBAN string.
        """
        iban = str(iban).replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            return False

        country_code = iban[:2]
        if country_code not in IBAN_FORMATS:
            return False

        if len(iban) != IBAN_FORMATS[country_code]:
            return False

        rearranged = iban[4:] + iban[:4]
        numeric_iban = ""
        for char in rearranged:
            if char.isdigit():
                numeric_iban += char
            elif char.isalpha():
                numeric_iban += str(ord(char) - ord('A') + 10)
            else:
                return False

        return int(numeric_iban) % 97 == 1

    def generate(self, country_code: str) -> str:
        """
        Generates a valid random IBAN for the given country code.
        """
        country_code = str(country_code).upper()
        if country_code not in IBAN_FORMATS:
            raise ValueError(f"Unsupported country code: {country_code}")

        length = IBAN_FORMATS[country_code]
        bban_length = length - 4
        chars = string.ascii_uppercase + string.digits
        bban = ''.join(random.choice(chars) for _ in range(bban_length)) # nosec B311

        temp_iban = country_code + "00" + bban
        rearranged = temp_iban[4:] + temp_iban[:4]

        numeric_iban = ""
        for char in rearranged:
            if char.isdigit():
                numeric_iban += char
            else:
                numeric_iban += str(ord(char) - ord('A') + 10)

        remainder = int(numeric_iban) % 97
        checksum = 98 - remainder

        checksum_str = str(checksum).zfill(2)
        return country_code + checksum_str + bban

    def parse(self, iban: str) -> dict:
        """
        Parses an IBAN into its components.
        """
        iban = str(iban).replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            raise ValueError("Invalid IBAN length")

        country_code = iban[:2]
        if country_code not in IBAN_FORMATS:
            raise ValueError(f"Unsupported country code: {country_code}")

        if len(iban) != IBAN_FORMATS[country_code]:
            raise ValueError(f"Invalid IBAN length for country {country_code}")

        checksum = iban[2:4]
        bban = iban[4:]

        is_valid = self.validate(iban)

        return {
            "iban": iban,
            "country_code": country_code,
            "checksum": checksum,
            "bban": bban,
            "is_valid": is_valid
        }

def run_iban_lab_logic(args):
    """
    CLI logic for the IBAN Lab.
    """
    manager = IbanManager()

    if args.action == "validate":
        is_valid = manager.validate(args.iban)
        if is_valid:
            print(f"✅ The IBAN '{args.iban}' is valid.")
            sys.exit(0)
        else:
            print(f"❌ The IBAN '{args.iban}' is INVALID.")
            sys.exit(1)

    elif args.action == "generate":
        try:
            generated = manager.generate(country_code=args.country_code)
            print(f"✅ Generated valid IBAN: {generated}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "parse":
        try:
            parsed = manager.parse(args.iban)
            print(f"IBAN: {parsed['iban']}")
            print(f"Country Code: {parsed['country_code']}")
            print(f"Checksum: {parsed['checksum']}")
            print(f"BBAN: {parsed['bban']}")
            print(f"Valid: {'Yes' if parsed['is_valid'] else 'No'}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
