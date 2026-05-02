import argparse
import json
import sys
from typing import Any, Dict, List
try:
    from faker import Faker
except ImportError:
    Faker = None


class FakerLabManager:
    """Manages the generation of fake data using Faker."""

    def __init__(self, locale: str = "en_US"):
        if Faker is None:
            raise ImportError("faker library not installed. Please install it using 'pip install faker'.")
        self.locale = locale
        try:
            self.fake = Faker(locale)
        except Exception:
            # Fallback if invalid locale
            self.fake = Faker("en_US")

    def generate_person(self, count: int = 1) -> List[Dict[str, Any]]:
        results = []
        for _ in range(count):
            results.append({
                "name": self.fake.name(),
                "address": self.fake.address(),
                "email": self.fake.email(),
                "phone": self.fake.phone_number(),
                "job": self.fake.job(),
                "company": self.fake.company(),
                "birthdate": self.fake.date_of_birth().isoformat()
            })
        return results

    def generate_internet(self, count: int = 1) -> List[Dict[str, Any]]:
        results = []
        for _ in range(count):
            results.append({
                "ipv4": self.fake.ipv4(),
                "ipv6": self.fake.ipv6(),
                "mac_address": self.fake.mac_address(),
                "uri": self.fake.uri(),
                "domain_name": self.fake.domain_name(),
                "user_name": self.fake.user_name(),
                "password": self.fake.password()
            })
        return results

    def generate_text(self, count: int = 1) -> List[str]:
        results = []
        for _ in range(count):
            results.append(self.fake.text())
        return results

    def generate_credit_card(self, count: int = 1) -> List[Dict[str, Any]]:
        results = []
        for _ in range(count):
            results.append({
                "provider": self.fake.credit_card_provider(),
                "number": self.fake.credit_card_number(),
                "expire": self.fake.credit_card_expire(),
                "security_code": self.fake.credit_card_security_code()
            })
        return results


def run_faker_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for faker lab."""
    locale = getattr(args, 'locale', 'en_US')
    manager = FakerLabManager(locale=locale)

    count = getattr(args, 'count', 1)

    try:
        if args.type == "person":
            result = manager.generate_person(count)
            print(json.dumps(result, indent=2))
            return True
        elif args.type == "internet":
            result = manager.generate_internet(count)
            print(json.dumps(result, indent=2))
            return True
        elif args.type == "text":
            result = manager.generate_text(count)
            for text in result:
                print(text)
                print("-" * 40)
            return True
        elif args.type == "credit_card":
            result = manager.generate_credit_card(count)
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Error: Unknown type '{args.type}'.", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error generating fake data: {e}", file=sys.stderr)
        return False
