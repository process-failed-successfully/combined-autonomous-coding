import sys
from typing import Dict, Any, Tuple

class VinManager:
    """
    Manages validation, decoding, and parsing of Vehicle Identification Numbers (VINs).
    Includes North American checksum validation.
    """

    # Transliteration values for letters to calculate the checksum
    TRANSLITERATION = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
        'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '0': 0
    }

    # Weights used in calculating the checksum based on the character's position
    WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]

    # Model year encoding characters (10th character)
    YEAR_CODES = {
        'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984, 'F': 1985, 'G': 1986, 'H': 1987, 'J': 1988, 'K': 1989,
        'L': 1990, 'M': 1991, 'N': 1992, 'P': 1993, 'R': 1994, 'S': 1995, 'T': 1996, 'V': 1997, 'W': 1998, 'X': 1999,
        'Y': 2000, '1': 2001, '2': 2002, '3': 2003, '4': 2004, '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
    }

    def validate(self, vin: str) -> bool:
        """
        Validates a given VIN string for correct length, allowed characters, and checksum (for North America).
        """
        if not vin:
            return False

        vin = str(vin).upper().strip()

        # VINs must be exactly 17 characters long
        if len(vin) != 17:
            return False

        # I, O, and Q are never used in VINs to avoid confusion with 1 and 0
        if any(c in "IOQ" for c in vin):
            return False

        # Basic allowed character check
        if any(c not in self.TRANSLITERATION.keys() for c in vin):
            return False

        return self._verify_checksum(vin)

    def _verify_checksum(self, vin: str) -> bool:
        """
        Verifies the checksum of the VIN (9th character).
        Returns True if valid or if it doesn't appear to be a North American VIN
        (in which case strict checksum validation might fail, but we'll try).
        """
        # North American VINs use the 9th character as a check digit
        check_char = vin[8]
        if check_char not in "0123456789X":
            # Might not be a NA VIN where checksum applies, but let's assume false for NA strictness
            pass

        sum_val = 0
        for i, char in enumerate(vin):
            sum_val += self.TRANSLITERATION[char] * self.WEIGHTS[i]

        remainder = sum_val % 11
        calculated_check = 'X' if remainder == 10 else str(remainder)

        return calculated_check == check_char

    def _guess_year(self, year_char: str, seventh_char: str) -> int:
        """
        Guesses the year based on the 10th character (year code) and the 7th character.
        VIN year codes cycle every 30 years.
        """
        if year_char not in self.YEAR_CODES:
            return -1

        base_year = self.YEAR_CODES[year_char]

        # According to standard ISO 3779, a numeric 7th character denotes the 1980–2009 cycle,
        # whereas an alphabetic 7th character indicates the 2010–2039 cycle.
        if seventh_char.isalpha():
            # 2010+ cycle (e.g., A = 2010 instead of 1980)
            base_year += 30

        return base_year

    def decode(self, vin: str) -> Dict[str, Any]:
        """
        Decodes a VIN into its constituent parts: WMI, VDS, VIS, Year, etc.
        """
        vin = str(vin).upper().strip()

        if len(vin) != 17 or any(c in "IOQ" for c in vin):
            raise ValueError("Invalid VIN format or length.")

        wmi = vin[0:3]
        vds = vin[3:9]
        vis = vin[9:17]

        year_char = vin[9]
        plant_char = vin[10]
        serial_number = vin[11:17]

        seventh_char = vin[6]

        year = self._guess_year(year_char, seventh_char)

        is_valid = self.validate(vin)

        # Simplified Region mapping based on the first character
        region = "Unknown"
        char1 = vin[0]
        if char1 in "12345":
            region = "North America"
        elif char1 in "S T U V W X Y Z".split():
            region = "Europe"
        elif char1 in "A B C D E F G H".split():
            region = "Africa"
        elif char1 in "J K L M N P R".split():
            region = "Asia"
        elif char1 in "6 7".split():
            region = "Oceania"
        elif char1 in "8 9".split():
            region = "South America"

        return {
            "vin": vin,
            "wmi": wmi,
            "vds": vds,
            "vis": vis,
            "year": year if year != -1 else "Unknown",
            "plant_code": plant_char,
            "serial_number": serial_number,
            "region": region,
            "is_valid": is_valid
        }

def run_vin_lab_logic(args):
    """
    CLI logic for the VIN Lab.
    """
    manager = VinManager()

    if args.action == "validate":
        is_valid = manager.validate(args.vin)
        if is_valid:
            print(f"✅ The VIN '{args.vin}' is valid (checksum verified).")
            sys.exit(0)
        else:
            print(f"❌ The VIN '{args.vin}' is INVALID.")
            sys.exit(1)

    elif args.action == "decode":
        try:
            decoded = manager.decode(args.vin)
            print(f"VIN: {decoded['vin']}")
            print(f"Valid: {'Yes' if decoded['is_valid'] else 'No'}")
            print(f"Region: {decoded['region']}")
            print(f"WMI (World Manufacturer Identifier): {decoded['wmi']}")
            print(f"VDS (Vehicle Descriptor Section): {decoded['vds']}")
            print(f"VIS (Vehicle Identifier Section): {decoded['vis']}")
            print(f"Estimated Year: {decoded['year']}")
            print(f"Plant Code: {decoded['plant_code']}")
            print(f"Serial Number: {decoded['serial_number']}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
