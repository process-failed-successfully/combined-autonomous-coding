import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

class VCardManager:
    """Manages vCard generation and parsing."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def generate_vcard(self, details: Dict[str, Any]) -> str:
        """Generates a vCard string from a dictionary of details."""
        lines = ["BEGIN:VCARD", "VERSION:3.0"]

        if "fn" in details:
            lines.append(f"FN:{details['fn']}")
        if "n" in details:
            lines.append(f"N:{details['n']}")
        if "org" in details:
            lines.append(f"ORG:{details['org']}")
        if "title" in details:
            lines.append(f"TITLE:{details['title']}")

        # Handle multiple emails
        if "email" in details:
            if isinstance(details["email"], list):
                for em in details["email"]:
                    lines.append(f"EMAIL;TYPE=INTERNET:{em}")
            else:
                 lines.append(f"EMAIL;TYPE=INTERNET:{details['email']}")

        # Handle multiple phones
        if "tel" in details:
             if isinstance(details["tel"], list):
                  for t in details["tel"]:
                      lines.append(f"TEL;TYPE=VOICE,CELL:{t}")
             else:
                  lines.append(f"TEL;TYPE=VOICE,CELL:{details['tel']}")

        if "url" in details:
            if isinstance(details["url"], list):
                 for u in details["url"]:
                     lines.append(f"URL:{u}")
            else:
                 lines.append(f"URL:{details['url']}")

        if "note" in details:
            # vcard notes escape newlines as \n
            note = details["note"].replace("\n", "\\n")
            lines.append(f"NOTE:{note}")

        if "adr" in details:
            # adr format: PO Box;Ext Addr;Street;City;State;Zip;Country
            lines.append(f"ADR:;;{details['adr']}")

        lines.append("END:VCARD")
        return "\n".join(lines)

    def parse_vcard(self, content: str) -> List[Dict[str, Any]]:
        """Parses a vCard string and returns a list of dictionaries."""
        vcards = []
        current_vcard = None

        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.upper() == "BEGIN:VCARD":
                current_vcard = {}
            elif line.upper() == "END:VCARD":
                if current_vcard is not None:
                    vcards.append(current_vcard)
                    current_vcard = None
            elif current_vcard is not None:
                # Handle folded lines (not fully compliant, but simple)
                if ":" not in line:
                     continue

                parts = line.split(":", 1)
                key_part = parts[0].upper()
                value = parts[1]

                # Extract base key (e.g., EMAIL;TYPE=INTERNET -> EMAIL)
                key = key_part.split(";")[0]

                if key in ["EMAIL", "TEL", "URL"]:
                    if key.lower() not in current_vcard:
                        current_vcard[key.lower()] = []
                    current_vcard[key.lower()].append(value)
                elif key == "ADR":
                    # Simple extraction, just taking the street part for now or full string
                    # Real adr has many semicolons
                    addr_parts = value.split(";")
                    # just join non empty
                    clean_addr = ", ".join([p for p in addr_parts if p])
                    current_vcard["adr"] = clean_addr
                elif key == "NOTE":
                     current_vcard["note"] = value.replace("\\n", "\n")
                else:
                    current_vcard[key.lower()] = value

        return vcards

def run_vcard_lab_logic(args: argparse.Namespace) -> bool:
    """Executes the vCard Lab CLI logic."""
    manager = VCardManager(args.project_dir)

    if args.action == "generate":
        details = {}
        if args.fn: details["fn"] = args.fn
        if args.n: details["n"] = args.n
        if args.org: details["org"] = args.org
        if args.title: details["title"] = args.title

        if args.email: details["email"] = args.email
        if args.tel: details["tel"] = args.tel
        if args.url: details["url"] = args.url

        if args.note: details["note"] = args.note
        if args.adr: details["adr"] = args.adr

        if not details:
            print("Error: No details provided for vCard generation.", file=sys.stderr)
            return False

        vcard_str = manager.generate_vcard(details)

        if args.output:
            try:
                out_path = Path(args.output)
                out_path.write_text(vcard_str, encoding="utf-8")
                print(f"vCard saved to {out_path}")
            except Exception as e:
                print(f"Error saving vCard: {e}", file=sys.stderr)
                return False
        else:
            print(vcard_str)
        return True

    elif args.action == "parse":
        if not args.file and not args.text:
            print("Error: --file or --text is required for parsing.", file=sys.stderr)
            return False

        content = ""
        if args.file:
            try:
                content = Path(args.file).read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                return False
        elif args.text:
            content = args.text

        try:
            vcards = manager.parse_vcard(content)
            if not vcards:
                print("No vCards found.")
            else:
                import json
                print(json.dumps(vcards, indent=2))
            return True
        except Exception as e:
             print(f"Error parsing vCard: {e}", file=sys.stderr)
             return False

    return False
