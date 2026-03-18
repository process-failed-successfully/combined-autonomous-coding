"""
VCard Lab
Provides utilities for generating and parsing vCard (.vcf) files.
"""
import sys
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VCardManager:
    """Manages VCard operations (generate/parse)."""

    def __init__(self):
        pass

    def generate(self, first_name: str, last_name: str, email: str = "", phone: str = "", org: str = "", title: str = "", url: str = "") -> str:
        """Generates a vCard 3.0 string."""
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{last_name};{first_name};;;",
            f"FN:{first_name} {last_name}".strip()
        ]
        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if phone:
            lines.append(f"TEL;TYPE=WORK,VOICE:{phone}")
        if email:
            lines.append(f"EMAIL;TYPE=PREF,INTERNET:{email}")
        if url:
            lines.append(f"URL:{url}")

        lines.append("END:VCARD")
        return "\n".join(lines)

    def parse(self, vcard_str: str) -> Dict[str, Any]:
        """Parses a simple vCard 3.0 string into a dictionary."""
        lines = vcard_str.strip().splitlines()
        result = {}
        if not lines or not lines[0].startswith("BEGIN:VCARD"):
            raise ValueError("Invalid vCard: Missing BEGIN:VCARD")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple splitting by first colon
            if ":" not in line:
                continue

            key_part, value = line.split(":", 1)
            # Handle parameters like TEL;TYPE=WORK,VOICE
            key = key_part.split(";")[0].upper()

            if key == "N":
                parts = value.split(";")
                result["last_name"] = parts[0] if len(parts) > 0 else ""
                result["first_name"] = parts[1] if len(parts) > 1 else ""
            elif key == "FN":
                result["full_name"] = value
            elif key == "ORG":
                result["org"] = value
            elif key == "TITLE":
                result["title"] = value
            elif key == "TEL":
                result["phone"] = value
            elif key == "EMAIL":
                result["email"] = value
            elif key == "URL":
                result["url"] = value
            elif key == "VERSION":
                result["version"] = value

        return result

def run_vcard_lab_logic(args) -> bool:
    """CLI logic for vcard-lab."""
    manager = VCardManager()

    if args.action == "generate":
        if not args.first_name and not args.last_name:
            print("Error: At least --first-name or --last-name is required.", file=sys.stderr)
            return False

        vcard = manager.generate(
            first_name=args.first_name or "",
            last_name=args.last_name or "",
            email=args.email or "",
            phone=args.phone or "",
            org=args.org or "",
            title=args.title or "",
            url=args.url or ""
        )
        print(vcard)

        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(vcard)
                print(f"Saved to {args.output}", file=sys.stderr)
            except IOError as e:
                print(f"Error writing to file: {e}", file=sys.stderr)
                return False
        return True

    elif args.action == "parse":
        vcard_content = ""
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    vcard_content = f.read()
            except IOError as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                return False
        else:
            if not sys.stdin.isatty():
                vcard_content = sys.stdin.read()
            else:
                print("Error: Provide a vCard via stdin or --file.", file=sys.stderr)
                return False

        if not vcard_content:
            print("Error: Empty vCard content.", file=sys.stderr)
            return False

        try:
            parsed = manager.parse(vcard_content)
            print(json.dumps(parsed, indent=2))
            return True
        except Exception as e:
            print(f"Error parsing vCard: {e}", file=sys.stderr)
            return False

    return False
