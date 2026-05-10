import sys
import re

class PhoneticLabManager:
    """Manages phonetic algorithms like Soundex."""

    def __init__(self) -> None:
        self._soundex_mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }

    def _soundex_word(self, word: str) -> str:
        """Computes the Soundex encoding for a single word."""
        if not word:
            return ""

        # Only process alphabetic characters
        word = re.sub(r'[^A-Z]', '', word.upper())
        if not word:
            return ""

        result = [word[0]]
        last_code = self._soundex_mapping.get(word[0], '0')

        for char in word[1:]:
            if len(result) == 4:
                break

            # W and H are ignored and don't break consecutive matching consonants
            if char in ('W', 'H'):
                continue

            code = self._soundex_mapping.get(char, '0')

            # Vowels (A, E, I, O, U, Y) are represented by '0', they break consonant sequences
            if code != last_code and code != '0':
                result.append(code)

            if code != '0':
                 last_code = code
            else:
                 # Vowel breaks the sequence
                 last_code = '0'

        # Pad with zeros if necessary
        while len(result) < 4:
            result.append('0')

        return "".join(result)

    def soundex(self, text: str) -> str:
        """Computes the Soundex encoding for each word in the input text."""
        words = text.split()
        return " ".join(self._soundex_word(word) for word in words if word)


def run_phonetic_lab_logic(args):
    """CLI logic for Phonetic Lab."""
    manager = PhoneticLabManager()

    if not args.text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        text = getattr(args, 'text', '')

    if not text:
        print("Error: Input text required either via --text or stdin.", file=sys.stderr)
        sys.exit(1)

    result = manager.soundex(text)
    print(result)
    sys.exit(0)
