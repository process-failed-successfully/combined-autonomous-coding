import base64
import html
import urllib.parse
import re
import difflib
import sys
from typing import Dict, Any
from collections import Counter


class TextLabManager:
    """Manages text transformation, encoding, analysis, and diffing."""

    def transform(self, text: str, type: str) -> str:
        if type == "upper":
            return text.upper()
        elif type == "lower":
            return text.lower()
        elif type == "title":
            return text.title()
        elif type == "camel":
            return self._to_camel(text)
        elif type == "snake":
            return self._to_snake(text)
        elif type == "kebab":
            return self._to_kebab(text)
        elif type == "pascal":
            return self._to_pascal(text)
        elif type == "constant":
            return self._to_constant(text)
        elif type == "dot":
            return self._to_dot(text)
        elif type == "path":
            return self._to_path(text)
        else:
            raise ValueError(f"Unknown transform type: {type}")

    def sort_lines(self, text: str, reverse: bool = False) -> str:
        lines = text.splitlines()
        lines.sort(reverse=reverse)
        return "\n".join(lines)

    def unique_lines(self, text: str) -> str:
        lines = text.splitlines()
        seen = set()
        result = []
        for line in lines:
            if line not in seen:
                result.append(line)
                seen.add(line)
        return "\n".join(result)

    def reverse_lines(self, text: str) -> str:
        lines = text.splitlines()
        return "\n".join(reversed(lines))

    def shuffle_lines(self, text: str) -> str:
        import random
        lines = text.splitlines()
        random.shuffle(lines)
        return "\n".join(lines)

    def number_lines(self, text: str) -> str:
        lines = text.splitlines()
        return "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))

    def trim_lines(self, text: str) -> str:
        lines = text.splitlines()
        return "\n".join(line.strip() for line in lines)

    def remove_empty_lines(self, text: str) -> str:
        lines = text.splitlines()
        return "\n".join(line for line in lines if line.strip())

    def collapse_spaces(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text)

    def filter_lines(self, text: str, pattern: str, exclude: bool = False) -> str:
        lines = text.splitlines()
        try:
            regex = re.compile(pattern)
        except re.error:
            return f"Error: Invalid Regex: {pattern}"

        result = []
        for line in lines:
            match = regex.search(line)
            if exclude:
                if not match:
                    result.append(line)
            else:
                if match:
                    result.append(line)
        return "\n".join(result)

    def encode(self, text: str, type: str, decode: bool = False) -> str:
        if type == "base64":
            if decode:
                return base64.b64decode(text.encode()).decode('utf-8', errors='replace')
            else:
                return base64.b64encode(text.encode()).decode('utf-8')
        elif type == "url":
            if decode:
                return urllib.parse.unquote(text)
            else:
                return urllib.parse.quote(text)
        elif type == "html":
            if decode:
                return html.unescape(text)
            else:
                return html.escape(text)
        elif type == "hex":
            if decode:
                return bytes.fromhex(text).decode('utf-8', errors='replace')
            else:
                return text.encode().hex()
        else:
            raise ValueError(f"Unknown encode type: {type}")

    def analyze(self, text: str) -> Dict[str, Any]:
        return {
            "length": len(text),
            "lines": len(text.splitlines()),
            "words": len(text.split()),
            "chars_no_space": len(text.replace(" ", "").replace("\n", "").replace("\t", "")),
            "frequency": Counter(text).most_common(5)
        }

    def diff(self, text1: str, text2: str) -> str:
        diff = difflib.unified_diff(
            text1.splitlines(),
            text2.splitlines(),
            fromfile="Text 1",
            tofile="Text 2",
            lineterm=""
        )
        return "\n".join(diff)

    def _to_camel(self, text: str) -> str:
        # split by space, underscore, hyphen
        words = re.split(r'[\s_\-]+', text)
        words = [w for w in words if w]  # remove empty
        if not words:
            return ""
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def _to_snake(self, text: str) -> str:
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        return re.sub(r'[\s\-]+', '_', text).lower()

    def _to_kebab(self, text: str) -> str:
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', text)
        return re.sub(r'[\s_]+', '-', text).lower()

    def _to_pascal(self, text: str) -> str:
        words = re.split(r'[\s_\-]+', text)
        words = [w for w in words if w]
        return "".join(w.capitalize() for w in words)

    def _to_constant(self, text: str) -> str:
        return self._to_snake(text).upper()

    def _to_dot(self, text: str) -> str:
        return self._to_snake(text).replace('_', '.')

    def _to_path(self, text: str) -> str:
        return self._to_snake(text).replace('_', '/')


def run_text_lab_logic(args):
    """CLI handler for Text Lab."""
    manager = TextLabManager()

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

    if args.action == "transform":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        try:
            print(manager.transform(text_input, args.type))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "encode":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        try:
            print(manager.encode(text_input, args.type, decode=args.decode))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "info":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        info = manager.analyze(text_input)
        print("--- Text Analysis ---")
        print(f"Length: {info['length']} chars")
        print(f"Lines:  {info['lines']}")
        print(f"Words:  {info['words']}")
        print(f"Chars (no space): {info['chars_no_space']}")
        print("Top 5 Chars:")
        for char, count in info['frequency']:
            display_char = repr(char)
            print(f"  {display_char}: {count}")

    elif args.action == "diff":
        if not args.text1 or not args.text2:
            print("Error: Two text inputs required for diff.", file=sys.stderr)
            return False
        print(manager.diff(args.text1, args.text2))

    elif args.action == "sort-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.sort_lines(text_input, reverse=args.reverse))

    elif args.action == "unique-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.unique_lines(text_input))

    elif args.action == "reverse-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.reverse_lines(text_input))

    elif args.action == "shuffle-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.shuffle_lines(text_input))

    elif args.action == "number-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.number_lines(text_input))

    elif args.action == "trim-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.trim_lines(text_input))

    elif args.action == "filter-lines":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        print(manager.filter_lines(text_input, args.pattern, exclude=args.exclude))

    return True
