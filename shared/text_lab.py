import base64
import html
import urllib.parse
import re
import difflib
import sys
import hashlib
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

    def extract(self, text: str, type: str) -> str:
        """Extracts patterns like emails, urls, ips, or embedded JSON from text."""
        import re
        if type == "email":
            # Basic email regex
            pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]*[a-zA-Z0-9-]+'
            matches = re.findall(pattern, text)
            return "\n".join(set(matches))
        elif type == "url":
            # Basic URL regex
            pattern = r'https?://[^\s]+'
            # remove trailing punctuation if matched
            matches = []
            for m in re.findall(pattern, text):
                while m and m[-1] in ".,;:!?()[]{}":
                    m = m[:-1]
                matches.append(m)
            return "\n".join(set(matches))
        elif type == "ip":
            # IPv4 regex
            pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            matches = re.findall(pattern, text)
            # Verify they are actual valid IPv4 ranges
            valid_ips = []
            for m in matches:
                parts = m.split('.')
                if all(0 <= int(p) <= 255 for p in parts):
                    valid_ips.append(m)
            return "\n".join(set(valid_ips))
        elif type == "json":
            return self._extract_json(text)
        else:
            raise ValueError(f"Unknown extract type: {type}")

    def _extract_json(self, text: str) -> str:
        """Finds and extracts valid JSON objects/arrays from arbitrary text."""
        import json
        extracted = []
        in_string = False
        escape_next = False
        bracket_count = 0
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    if brace_count == 0 and bracket_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    if brace_count > 0:
                        brace_count -= 1
                        if brace_count == 0 and bracket_count == 0 and start_idx != -1:
                            potential_json = text[start_idx:i+1]
                            try:
                                parsed = json.loads(potential_json)
                                extracted.append(json.dumps(parsed, indent=2))
                            except json.JSONDecodeError:
                                pass
                            start_idx = -1
                elif char == '[':
                    if bracket_count == 0 and brace_count == 0:
                        start_idx = i
                    bracket_count += 1
                elif char == ']':
                    if bracket_count > 0:
                        bracket_count -= 1
                        if bracket_count == 0 and brace_count == 0 and start_idx != -1:
                            potential_json = text[start_idx:i+1]
                            try:
                                parsed = json.loads(potential_json)
                                extracted.append(json.dumps(parsed, indent=2))
                            except json.JSONDecodeError:
                                pass
                            start_idx = -1

        if not extracted:
            return ""
        return "\n\n".join(extracted)

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

    def hash_text(self, text: str, algorithm: str) -> str:
        algo = algorithm.lower()
        if algo not in hashlib.algorithms_available:
            raise ValueError(f"Unknown hash algorithm: {algo}")

        h = hashlib.new(algo)
        h.update(text.encode('utf-8'))
        return h.hexdigest()

    def diff(self, text1: str, text2: str) -> str:
        diff = difflib.unified_diff(
            text1.splitlines(),
            text2.splitlines(),
            fromfile="Text 1",
            tofile="Text 2",
            lineterm=""
        )
        return "\n".join(diff)

    def distance(self, text1: str, text2: str, algo: str = "levenshtein") -> int:
        algo = algo.lower()
        if algo == "levenshtein":
            m, n = len(text1), len(text2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]

            for i in range(m + 1):
                for j in range(n + 1):
                    if i == 0:
                        dp[i][j] = j
                    elif j == 0:
                        dp[i][j] = i
                    elif text1[i - 1] == text2[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1]
                    else:
                        dp[i][j] = 1 + min(dp[i][j - 1],      # Insert
                                           dp[i - 1][j],      # Remove
                                           dp[i - 1][j - 1])  # Replace
            return dp[m][n]
        else:
            raise ValueError(f"Unknown distance algorithm: {algo}")

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

    def lorem_ipsum(self, words: int = 100) -> str:
        import random
        lorem_words = [
            "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
            "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
            "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud", "exercitation",
            "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea", "commodo", "consequat",
            "duis", "aute", "irure", "dolor", "in", "reprehenderit", "in", "voluptate", "velit",
            "esse", "cillum", "dolore", "eu", "fugiat", "nulla", "pariatur", "excepteur", "sint",
            "occaecat", "cupidatat", "non", "proident", "sunt", "in", "culpa", "qui", "officia",
            "deserunt", "mollit", "anim", "id", "est", "laborum"
        ]

        if words <= 0:
            return ""

        result = []
        for i in range(words):
            word = random.choice(lorem_words)
            if i == 0:
                word = word.capitalize()
            elif i > 0 and result[-1].endswith('.'):
                word = word.capitalize()

            # Randomly add periods to simulate sentences
            if i > 5 and i < words - 1 and random.random() < 0.1 and not word.endswith('.'):
                word += '.'

            result.append(word)

        text = " ".join(result)
        if not text.endswith('.'):
            text += '.'
        return text

    def generate_random_string(self, length: int = 16, charset: str = "alphanumeric") -> str:
        import random
        import string

        if length <= 0:
            return ""

        if charset == "alphanumeric":
            chars = string.ascii_letters + string.digits
        elif charset == "alpha":
            chars = string.ascii_letters
        elif charset == "numeric":
            chars = string.digits
        elif charset == "hex":
            chars = "0123456789abcdef"
        elif charset == "ascii":
            chars = string.printable.strip()
        else:
            raise ValueError(f"Unknown charset: {charset}")

        # Use secrets if available for better security
        try:
            import secrets
            return "".join(secrets.choice(chars) for _ in range(length))
        except ImportError:
            return "".join(random.choice(chars) for _ in range(length))



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

    if args.action == "extract":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        try:
            print(manager.extract(text_input, args.type))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "transform":
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

    elif args.action == "hash":
        text_input = get_input(args.text)
        if not text_input:
            print("Error: Input text required (argument or stdin).", file=sys.stderr)
            return False
        try:
            print(manager.hash_text(text_input, args.algo))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "lorem":
        words = args.words if hasattr(args, "words") and args.words is not None else 100
        print(manager.lorem_ipsum(words))

    elif args.action in ("random", "rand"):
        length = args.length if hasattr(args, "length") and args.length is not None else 16
        charset = args.charset if hasattr(args, "charset") and args.charset is not None else "alphanumeric"
        try:
            print(manager.generate_random_string(length, charset))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "distance":
        if args.text1 is None or args.text2 is None:
            print("Error: Two text inputs required for distance.", file=sys.stderr)
            return False
        try:
            print(manager.distance(args.text1, args.text2, getattr(args, 'algo', 'levenshtein')))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    return True
