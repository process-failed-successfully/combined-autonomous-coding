import unicodedata
import sys
import argparse
from typing import List, Dict, Any, Optional

class UniLabManager:
    """Manages Unicode Lab operations: inspect, search, escape, and unescape."""

    def inspect(self, text: str) -> List[Dict[str, str]]:
        """
        Returns detailed information about each character in the text.
        Includes char, code point, name, category, and hex encodings.
        """
        results = []
        for char in text:
            try:
                name = unicodedata.name(char)
            except ValueError:
                name = "<no name>"

            try:
                category = unicodedata.category(char)
            except ValueError:
                category = "Unknown"

            results.append({
                "char": char,
                "code_point": f"U+{ord(char):04X}",
                "name": name,
                "category": category,
                "utf8": char.encode('utf-8').hex().upper(),
                "utf16": char.encode('utf-16be').hex().upper(),
            })
        return results

    def search(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Searches for Unicode characters whose names contain the query string.
        Iterates through all Unicode code points (0x0 to 0x10FFFF).
        """
        query = query.upper()
        results = []
        count = 0

        # Optimize: If query is single char, just lookup that char? No, user wants search by name.

        for i in range(0x110000):
            char = chr(i)
            try:
                name = unicodedata.name(char)
                if query in name:
                    results.append({
                        "char": char,
                        "code_point": f"U+{i:04X}",
                        "name": name
                    })
                    count += 1
                    if count >= limit:
                        break
            except ValueError:
                pass

        return results

    def escape(self, text: str) -> str:
        """Escapes non-ASCII characters to \\uXXXX or \\UXXXXXXXX sequences."""
        return text.encode('ascii', 'backslashreplace').decode('utf-8')

    def unescape(self, text: str) -> str:
        """Unescapes \\uXXXX and \\UXXXXXXXX sequences."""
        # codecs.decode with 'unicode_escape' handles standard escapes
        try:
            return text.encode('utf-8').decode('unicode_escape')
        except Exception:
            # Fallback to returning original if decoding fails (e.g. invalid escape)
            return text

def run_uni_lab_logic(args) -> bool:
    """CLI handler for Unicode Lab."""
    manager = UniLabManager()

    # Helper to get input
    def get_input(arg_val):
        if arg_val:
            return arg_val
        # Try stdin
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read().strip()
            except Exception:
                pass
        return None

    if args.action == "inspect":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False

        data = manager.inspect(text_input)

        # Header
        header = f"{'Char':<6} | {'Code':<9} | {'Cat':<4} | {'UTF-8':<8} | {'Name'}"
        print(header)
        print("-" * len(header))

        for item in data:
            # Handle control characters or invisible chars for display
            display_char = item['char']
            if unicodedata.category(item['char']).startswith('C'):
                display_char = '' # Replacement char for control codes
            elif display_char.isspace():
                if display_char == ' ':
                    display_char = "' '"
                else:
                    display_char = repr(display_char)

            print(f"{display_char:<6} | {item['code_point']:<9} | {item['category']:<4} | {item['utf8']:<8} | {item['name']}")

    elif args.action == "search":
        if not args.query:
            print("Error: Query required.", file=sys.stderr)
            return False

        print(f"Searching for '{args.query}' (limit: {args.limit})...")
        results = manager.search(args.query, limit=args.limit)

        if not results:
            print("No results found.")
        else:
            print(f"Found {len(results)} matches:")
            for res in results:
                print(f"{res['char']}  {res['code_point']}  {res['name']}")

    elif args.action == "escape":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required.", file=sys.stderr)
            return False
        print(manager.escape(text_input))

    elif args.action == "unescape":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required.", file=sys.stderr)
            return False
        print(manager.unescape(text_input))

    return True
