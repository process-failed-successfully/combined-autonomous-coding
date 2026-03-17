import sys
import argparse
import re

class NatoLabManager:
    """
    Manages translation between standard text and the NATO Phonetic Alphabet.
    """

    NATO_ALPHABET = {
        'A': 'Alfa', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
        'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliett',
        'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
        'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
        'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee',
        'Z': 'Zulu',
        '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
        '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine'
    }

    # Support common variations and aliases
    NATO_ALIASES = {
        'alpha': 'A', 'juliet': 'J', 'xray': 'X', 'x-ray': 'X',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
        '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    }

    REVERSE_NATO = {v.lower(): k for k, v in NATO_ALPHABET.items()}
    REVERSE_NATO.update(NATO_ALIASES)

    def encode(self, text: str) -> str:
        """
        Translates a string into the NATO phonetic alphabet.
        Characters not in the alphabet are preserved.
        Double spaces are used to separate original words for readability.
        """
        words = []
        for word in text.split(" "):
            encoded_word = []
            for char in word:
                upper_char = char.upper()
                if upper_char in self.NATO_ALPHABET:
                    encoded_word.append(self.NATO_ALPHABET[upper_char])
                else:
                    encoded_word.append(char)
            # Join characters within a word by a single space
            words.append(" ".join(encoded_word))

        # Join the original words with a double space or appropriate delimiter
        return "  ".join(words)

    def decode(self, text: str) -> str:
        """
        Translates NATO phonetic alphabet words back into a string.
        Attempts to reconstruct original spacing based on multiple spaces.
        """
        # Split by double spaces first to identify original words
        original_words = re.split(r' {2,}', text)

        decoded_words = []
        for original_word in original_words:
            # Within an original word, split by single spaces or mixed punctuation
            # To handle punctuation like "Oscar!", we tokenize.
            tokens = re.split(r'(\s+)', original_word)

            reconstructed_word = ""
            for token in tokens:
                if not token or token.isspace():
                    continue

                # Strip out punctuation to check against reverse map
                m = re.match(r'^([^A-Za-z0-9]*)([A-Za-z0-9\-]+)([^A-Za-z0-9]*)$', token)
                if m:
                    pre, word, post = m.groups()
                    lower_word = word.lower()
                    if lower_word in self.REVERSE_NATO:
                        reconstructed_word += pre + self.REVERSE_NATO[lower_word] + post
                    else:
                        # For unmapped tokens (like "HELLO" directly provided), append directly
                        # but keep surrounding punctuation if any
                        reconstructed_word += token
                else:
                    reconstructed_word += token
            decoded_words.append(reconstructed_word)

        return " ".join(decoded_words)


def run_nato_lab_logic(args: argparse.Namespace) -> bool:
    """
    CLI handler for NATO Phonetic Alphabet Lab.
    """
    manager = NatoLabManager()

    try:
        if getattr(args, "encode", None):
            encoded = manager.encode(args.encode)
            print(encoded)
        elif getattr(args, "decode", None):
            decoded = manager.decode(args.decode)
            print(decoded)
        else:
            print("Error: must provide either --encode, --decode, or --tui", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error processing NATO phonetic alphabet: {e}", file=sys.stderr)
        return False
