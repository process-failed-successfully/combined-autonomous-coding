import sys
import base64
import urllib.parse
import html
import codecs
import collections
import re
import difflib
from pathlib import Path

class TextLabManager:
    """
    Manager for Text Lab utilities: transform, encode, decode, analyze, diff.
    """

    def transform(self, text: str, case_type: str) -> str:
        """Transforms text case."""
        if not text:
            return ""

        if case_type == "upper":
            return text.upper()
        elif case_type == "lower":
            return text.lower()
        elif case_type == "title":
            return text.title()
        elif case_type == "alternating":
            return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))

        # Complex cases requiring splitting
        # Split by non-alphanumeric, or by camelCase boundary
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+', text)
        if not words:
            # Fallback for simple split if regex misses
             words = re.split(r'[^a-zA-Z0-9]', text)

        # Filter empty
        words = [w for w in words if w]

        if case_type == "camel":
            return words[0].lower() + "".join(w.capitalize() for w in words[1:])
        elif case_type == "pascal":
            return "".join(w.capitalize() for w in words)
        elif case_type == "snake":
            return "_".join(w.lower() for w in words)
        elif case_type == "kebab":
            return "-".join(w.lower() for w in words)
        elif case_type == "constant":
            return "_".join(w.upper() for w in words)
        else:
            return text

    def encode(self, text: str, encoding_type: str) -> str:
        """Encodes text."""
        if encoding_type == "base64":
            return base64.b64encode(text.encode("utf-8")).decode("utf-8")
        elif encoding_type == "url":
            return urllib.parse.quote(text)
        elif encoding_type == "html":
            return html.escape(text)
        elif encoding_type == "hex":
            return text.encode("utf-8").hex()
        elif encoding_type == "rot13":
            return codecs.encode(text, "rot_13")
        return text

    def decode(self, text: str, encoding_type: str) -> str:
        """Decodes text."""
        try:
            if encoding_type == "base64":
                return base64.b64decode(text).decode("utf-8")
            elif encoding_type == "url":
                return urllib.parse.unquote(text)
            elif encoding_type == "html":
                return html.unescape(text)
            elif encoding_type == "hex":
                return bytes.fromhex(text).decode("utf-8")
            elif encoding_type == "rot13":
                return codecs.decode(text, "rot_13")
        except Exception as e:
            return f"Error decoding: {e}"
        return text

    def analyze(self, text: str) -> dict:
        """Analyzes text statistics."""
        chars = len(text)
        lines = len(text.splitlines())
        words_list = re.findall(r'\w+', text.lower())
        words_count = len(words_list)

        most_common = []
        if words_list:
            counter = collections.Counter(words_list)
            most_common = counter.most_common(5)

        return {
            "chars": chars,
            "lines": lines,
            "words": words_count,
            "most_common": most_common
        }

    def diff(self, text1: str, text2: str) -> str:
        """Generates a unified diff."""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        diff = difflib.unified_diff(
            lines1, lines2,
            fromfile="Text 1", tofile="Text 2",
            lineterm=""
        )
        return "\n".join(diff)

def run_text_lab_logic(args):
    """CLI Logic for Text Lab."""
    manager = TextLabManager()

    # Get input text
    text = ""
    if hasattr(args, 'text') and args.text:
        text = args.text
    elif hasattr(args, 'file') and args.file:
        try:
            path = Path(args.file)
            if not path.exists():
                print(f"Error: File '{path}' not found.", file=sys.stderr)
                sys.exit(1)
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # For diff, we need a second input
    text2 = ""
    if args.action == "diff":
        if hasattr(args, 'text2') and args.text2:
            text2 = args.text2
        elif hasattr(args, 'file2') and args.file2:
             try:
                path2 = Path(args.file2)
                if not path2.exists():
                    print(f"Error: File '{path2}' not found.", file=sys.stderr)
                    sys.exit(1)
                text2 = path2.read_text(encoding="utf-8")
             except Exception as e:
                print(f"Error reading file 2: {e}", file=sys.stderr)
                sys.exit(1)

        # If text/file 1 is missing for diff
        if not text and not (hasattr(args, 'file') and args.file):
             # Try stdin? Or just require args
             print("Error: Input text required for diff (use --text or --file).", file=sys.stderr)
             sys.exit(1)

    # If no text provided (and not diff which handled it), try stdin for pipe support?
    if not text and args.action != "diff":
        if not sys.stdin.isatty():
            try:
                text = sys.stdin.read()
            except Exception:
                pass

    if not text and args.action != "diff":
         print("Error: Input text required (use --text, --file, or pipe).", file=sys.stderr)
         sys.exit(1)

    # Actions
    if args.action == "transform":
        result = manager.transform(text, args.type)
        print(result)

    elif args.action == "encode":
        result = manager.encode(text, args.type)
        print(result)

    elif args.action == "decode":
        result = manager.decode(text, args.type)
        print(result)

    elif args.action == "analyze":
        stats = manager.analyze(text)
        print("--- Text Analysis ---")
        print(f"Characters: {stats['chars']}")
        print(f"Words:      {stats['words']}")
        print(f"Lines:      {stats['lines']}")
        print("Most Common Words:")
        for word, count in stats['most_common']:
            print(f"  {word}: {count}")

    elif args.action == "diff":
        diff_output = manager.diff(text, text2)
        if diff_output:
            print(diff_output)
        else:
            print("Texts are identical.")

    return True
