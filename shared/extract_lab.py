import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

class ExtractLabManager:
    """Manages the extraction of specific patterns (IoCs, emails, IPs, etc.) from text."""

    # Pre-defined regular expressions
    PATTERNS = {
        "ipv4": r"(?:\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}\b",
        # Broad IPv6 matching
        "ipv6": r"(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}|(?:[a-fA-F0-9]{1,4}:){1,7}:|::(?:[a-fA-F0-9]{1,4}:){0,7}[a-fA-F0-9]{1,4}",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        # Loose URL matching
        "url": r"\bhttps?://(?:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|localhost)(?::[0-9]+)?(?:/[a-zA-Z0-9-._~:/?#[\]@!$&'()*+,;=%]*)*\b",
        "domain": r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,})\b",
        "mac": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b",
        "md5": r"\b[a-fA-F0-9]{32}\b",
        "sha1": r"\b[a-fA-F0-9]{40}\b",
        "sha256": r"\b[a-fA-F0-9]{64}\b",
        "uuid": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        "btc": r"\b(?:1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b",
        # Simple credit card matching (13-19 digits, optionally separated by spaces or dashes)
        "creditcard": r"\b(?:\d[ -]*?){13,16}\b",
        "date": r"\b(?:19|20)\d\d[- /.](?:0[1-9]|1[012])[- /.](?:0[1-9]|[12][0-9]|3[01])\b"
    }

    def extract(self, text: str, extract_type: str, unique: bool = True) -> List[str]:
        """Extracts a specific type of pattern from the given text."""
        extract_type = extract_type.lower()
        if extract_type not in self.PATTERNS:
            raise ValueError(f"Unknown extract type: {extract_type}. Available types: {', '.join(self.PATTERNS.keys())}")

        pattern = self.PATTERNS[extract_type]
        matches = re.findall(pattern, text)

        # Clean up some specific matches
        if extract_type == "creditcard":
            # Just verify it's mostly digits and a reasonable length after stripping spaces/dashes
            valid_ccs = []
            for match in matches:
                clean = re.sub(r"[ -]", "", match)
                if 13 <= len(clean) <= 19 and clean.isdigit():
                    valid_ccs.append(clean)
            matches = valid_ccs

        # Optional domain cleanup (avoid returning "http://domain.com" as domain when matching just domain)
        # The domain regex handles standard domains but we want to ensure we don't accidentally match parts of emails or URLs with extra baggage unless intended.
        # It's okay as is for basic use.

        if unique:
            # Preserve order while deduplicating
            seen = set()
            unique_matches = []
            for m in matches:
                if m not in seen:
                    seen.add(m)
                    unique_matches.append(m)
            return unique_matches

        return matches

    def extract_all(self, text: str, unique: bool = True) -> Dict[str, List[str]]:
        """Extracts all known pattern types from the given text."""
        results = {}
        for extract_type in self.PATTERNS.keys():
            matches = self.extract(text, extract_type, unique=unique)
            if matches:
                results[extract_type] = matches
        return results

    def get_supported_types(self) -> List[str]:
        """Returns a list of supported extraction types."""
        return list(self.PATTERNS.keys())

def run_extract_lab_logic(args):
    """CLI logic for Extract Lab."""
    manager = ExtractLabManager()

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Extract Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-extract")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if getattr(args, '_in_event_loop', False) or (loop and loop.is_running()):
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return

    # Check inputs
    text = ""
    if getattr(args, "text", None):
        text = args.text
    elif getattr(args, "file", None):
        try:
            text = Path(args.file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)

    if not text:
        print("Error: Input text is required via --text or --file.", file=sys.stderr)
        sys.exit(1)

    extract_type = getattr(args, "type", "all").lower()
    unique = getattr(args, "unique", False)

    try:
        if extract_type == "all":
            results = manager.extract_all(text, unique=unique)
            if getattr(args, "json", False):
                print(json.dumps(results, indent=2))
            else:
                if not results:
                    print("No matches found.")
                else:
                    for k, v in results.items():
                        print(f"--- {k.upper()} ({len(v)}) ---")
                        for item in v:
                            print(item)
                        print()
        else:
            results = manager.extract(text, extract_type, unique=unique)
            if getattr(args, "json", False):
                print(json.dumps(results, indent=2))
            else:
                if not results:
                    print(f"No {extract_type} matches found.")
                else:
                    for item in results:
                        print(item)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
