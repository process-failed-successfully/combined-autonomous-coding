import sys
import argparse
from typing import Dict, Any, List

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False


class PhoneLabManager:
    """Manages phone number operations: parse, validate, format, info."""

    def __init__(self):
        if not PHONENUMBERS_AVAILABLE:
            raise ImportError("The 'phonenumbers' library is required for PhoneLab. Install it with: pip install phonenumbers")

    def _type_to_string(self, p_type: int) -> str:
        """Converts phonenumbers type enum to string."""
        mapping = {
            PhoneNumberType.FIXED_LINE: "Fixed Line",
            PhoneNumberType.MOBILE: "Mobile",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            PhoneNumberType.TOLL_FREE: "Toll Free",
            PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            PhoneNumberType.SHARED_COST: "Shared Cost",
            PhoneNumberType.VOIP: "VOIP",
            PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
            PhoneNumberType.PAGER: "Pager",
            PhoneNumberType.UAN: "UAN",
            PhoneNumberType.VOICEMAIL: "Voicemail",
            PhoneNumberType.UNKNOWN: "Unknown"
        }
        return mapping.get(p_type, "Unknown")

    def parse(self, phone: str, region: str = None) -> Any:
        """Parses a phone number string."""
        try:
            return phonenumbers.parse(phone, region)
        except phonenumbers.NumberParseException as e:
            raise ValueError(f"Failed to parse phone number: {e}")

    def is_valid(self, phone: str, region: str = None) -> bool:
        """Checks if a phone number is valid."""
        try:
            parsed = self.parse(phone, region)
            return phonenumbers.is_valid_number(parsed)
        except ValueError:
            return False

    def format(self, phone: str, region: str = None, fmt_type: str = "international") -> str:
        """Formats a phone number."""
        parsed = self.parse(phone, region)

        if fmt_type.lower() == "e164":
            fmt = phonenumbers.PhoneNumberFormat.E164
        elif fmt_type.lower() == "national":
            fmt = phonenumbers.PhoneNumberFormat.NATIONAL
        elif fmt_type.lower() == "rfc3966":
            fmt = phonenumbers.PhoneNumberFormat.RFC3966
        else:
            fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL

        return phonenumbers.format_number(parsed, fmt)

    def get_info(self, phone: str, region: str = None) -> Dict[str, Any]:
        """Extracts detailed information from a phone number."""
        parsed = self.parse(phone, region)

        info = {
            "valid": phonenumbers.is_valid_number(parsed),
            "possible": phonenumbers.is_possible_number(parsed),
            "country_code": parsed.country_code,
            "national_number": parsed.national_number,
            "extension": parsed.extension,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "rfc3966": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966),
        }

        if info["valid"]:
            p_type = number_type(parsed)
            info["type"] = self._type_to_string(p_type)

            # Region (Country)
            info["region_code"] = phonenumbers.region_code_for_number(parsed)
            info["location"] = geocoder.description_for_number(parsed, "en")

            # Carrier (mostly for mobile numbers)
            info["carrier"] = carrier.name_for_number(parsed, "en")

            # Timezones
            timezones = timezone.time_zones_for_number(parsed)
            info["timezones"] = list(timezones)
        else:
            info["type"] = "Unknown"
            info["region_code"] = None
            info["location"] = ""
            info["carrier"] = ""
            info["timezones"] = []

        return info


def run_phone_lab_logic(args: argparse.Namespace):
    """CLI handler for Phone Lab."""
    try:
        manager = PhoneLabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    region = getattr(args, 'region', None)

    if args.action == "parse":
        try:
            parsed = manager.parse(args.phone, region)
            print(parsed)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "format":
        try:
            fmt_type = getattr(args, 'format', 'international')
            formatted = manager.format(args.phone, region, fmt_type)
            print(formatted)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        is_valid = manager.is_valid(args.phone, region)
        if is_valid:
            print(f"✅ Valid Phone Number: {args.phone}")
            sys.exit(0)
        else:
            print(f"❌ Invalid Phone Number: {args.phone}")
            sys.exit(1)

    elif args.action == "info":
        try:
            info = manager.get_info(args.phone, region)

            print(f"--- Phone Lookup: {args.phone} ---")
            print(f"  Valid: {info['valid']}")
            print(f"  Possible: {info['possible']}")
            if info["valid"] or info["possible"]:
                print(f"  Country Code: +{info['country_code']}")
                print(f"  National Number: {info['national_number']}")
                if info["extension"]:
                    print(f"  Extension: {info['extension']}")
                print(f"  Formats:")
                print(f"    E164: {info['e164']}")
                print(f"    International: {info['international']}")
                print(f"    National: {info['national']}")
                print(f"    RFC3966: {info['rfc3966']}")

            if info["valid"]:
                print(f"  Type: {info['type']}")
                print(f"  Region Code: {info['region_code']}")
                print(f"  Location: {info['location'] or 'N/A'}")
                print(f"  Carrier: {info['carrier'] or 'N/A'}")
                if info["timezones"]:
                    print(f"  Timezones: {', '.join(info['timezones'])}")

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
