import re
import sys


class StringCaseManager:
    """Manages string case conversions."""

    def __init__(self) -> None:
        pass

    def _split_into_words(self, text: str) -> list[str]:
        """Splits a string into words based on spaces, underscores, hyphens, and camelCase boundaries."""
        # First, split by spaces, underscores, and hyphens
        parts = re.split(r'[\s_\-]+', text)

        words = []
        for part in parts:
            if not part:
                continue
            # Split camelCase and PascalCase
            # This regex matches a lowercase letter followed by an uppercase letter, or
            # a sequence of uppercase letters followed by an uppercase and a lowercase letter (e.g., XMLHttp -> XML Http)
            sub_parts = re.sub(r'([a-z])([A-Z])', r'\1 \2', part)
            sub_parts = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', sub_parts)
            words.extend([w for w in sub_parts.split(' ') if w])

        return words

    def to_camel(self, text: str) -> str:
        """Converts string to camelCase."""
        words = self._split_into_words(text)
        if not words:
            return ""
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def to_snake(self, text: str) -> str:
        """Converts string to snake_case."""
        words = self._split_into_words(text)
        return "_".join(w.lower() for w in words)

    def to_kebab(self, text: str) -> str:
        """Converts string to kebab-case."""
        words = self._split_into_words(text)
        return "-".join(w.lower() for w in words)

    def to_pascal(self, text: str) -> str:
        """Converts string to PascalCase."""
        words = self._split_into_words(text)
        return "".join(w.capitalize() for w in words)

    def to_constant(self, text: str) -> str:
        """Converts string to CONSTANT_CASE."""
        words = self._split_into_words(text)
        return "_".join(w.upper() for w in words)

    def to_dot(self, text: str) -> str:
        """Converts string to dot.case."""
        words = self._split_into_words(text)
        return ".".join(w.lower() for w in words)

    def to_path(self, text: str) -> str:
        """Converts string to path/case."""
        words = self._split_into_words(text)
        return "/".join(w.lower() for w in words)


def run_string_case_lab_logic(args):
    """CLI logic for String Case Lab."""
    manager = StringCaseManager()

    if not args.text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        text = args.text

    if not text:
        print("Error: Input text required either via --text or stdin.", file=sys.stderr)
        sys.exit(1)

    result = ""
    mode = args.to.lower()

    if mode == "camel":
        result = manager.to_camel(text)
    elif mode == "snake":
        result = manager.to_snake(text)
    elif mode == "kebab":
        result = manager.to_kebab(text)
    elif mode == "pascal":
        result = manager.to_pascal(text)
    elif mode == "constant":
        result = manager.to_constant(text)
    elif mode == "dot":
        result = manager.to_dot(text)
    elif mode == "path":
        result = manager.to_path(text)
    else:
        print(f"Unknown target case format: {mode}", file=sys.stderr)
        sys.exit(1)

    print(result)
    sys.exit(0)
