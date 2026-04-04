import re
import sys


class RegexEscapeManager:
    """Manager for Regex escaping and unescaping."""

    def escape(self, text: str) -> str:
        """Escapes a string so it can be used literally in a regex."""
        if not text:
            return ""
        return re.escape(text)

    def unescape(self, text: str) -> str:
        """
        Unescapes a regex string.
        It removes the backslash character before any non-alphanumeric character.
        Note: This is a best-effort simple unescape for literal strings that were
        escaped with re.escape.
        """
        if not text:
            return ""

        # re.escape usually escapes non-alphanumeric chars.
        # So we want to replace `\c` with `c` where `c` is non-alphanumeric.
        # But for general use, we can simply replace `\c` with `c` for any char
        # except when it's a special escape sequence like \n, \t which shouldn't happen
        # from a standard literal re.escape, but just in case we only unescape punctuation.

        # Instead of complex regex, iterate through chars
        result = []
        i = 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                # re.escape currently escapes all non-ASCII letters/numbers in Python < 3.3
                # and only punctuation in Python >= 3.3.
                # In Python 3.7+, it only escapes characters that might have special meaning.
                # To be safe, we just strip the backslash.
                # Wait, what if it's \n? re.escape('\n') -> '\\\n'

                # So we simply skip the backslash and append the next character
                result.append(text[i+1])
                i += 2
            else:
                result.append(text[i])
                i += 1

        return "".join(result)


def run_regex_escape_lab_logic(args) -> bool:
    """CLI logic for Regex Escape Lab."""
    manager = RegexEscapeManager()

    if hasattr(args, 'encode') and args.encode:
        print(manager.escape(args.encode))
        return True
    elif hasattr(args, 'decode') and args.decode:
        print(manager.unescape(args.decode))
        return True
    else:
        print("Error: No action specified. Use --encode or --decode.", file=sys.stderr)
        return False
