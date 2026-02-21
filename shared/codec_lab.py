import base64
import binascii
import codecs
import html
import urllib.parse


class CodecLabManager:
    """Manager for various text encoding/decoding operations."""

    def __init__(self) -> None:
        pass

    def base64_encode(self, text: str) -> str:
        """Encodes text to Base64."""
        if not text:
            return ""
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    def base64_decode(self, text: str) -> str:
        """Decodes Base64 text."""
        if not text:
            return ""
        try:
            return base64.b64decode(text).decode("utf-8")
        except binascii.Error as e:
            return f"Error: Invalid Base64 string ({e})"
        except UnicodeDecodeError as e:
            return f"Error: Decoded bytes are not valid UTF-8 ({e})"

    def rot13(self, text: str) -> str:
        """Rotates characters by 13 positions."""
        if not text:
            return ""
        return codecs.encode(text, "rot_13")

    def html_encode(self, text: str) -> str:
        """Escapes HTML entities."""
        if not text:
            return ""
        return html.escape(text)

    def html_decode(self, text: str) -> str:
        """Unescapes HTML entities."""
        if not text:
            return ""
        return html.unescape(text)

    def url_encode(self, text: str) -> str:
        """URL encodes text."""
        if not text:
            return ""
        return urllib.parse.quote(text)

    def url_decode(self, text: str) -> str:
        """URL decodes text."""
        if not text:
            return ""
        return urllib.parse.unquote(text)

    def hex_encode(self, text: str) -> str:
        """Encodes text to Hexadecimal string."""
        if not text:
            return ""
        return text.encode("utf-8").hex()

    def hex_decode(self, text: str) -> str:
        """Decodes Hexadecimal string."""
        if not text:
            return ""
        try:
            # Remove spaces if any
            clean_text = text.replace(" ", "")
            return bytes.fromhex(clean_text).decode("utf-8")
        except ValueError as e:
            return f"Error: Invalid Hex string ({e})"
        except UnicodeDecodeError as e:
            return f"Error: Decoded bytes are not valid UTF-8 ({e})"

    def binary_encode(self, text: str) -> str:
        """Encodes text to binary string (0s and 1s)."""
        if not text:
            return ""
        return " ".join(format(ord(c), "08b") for c in text)

    def binary_decode(self, text: str) -> str:
        """Decodes binary string."""
        if not text:
            return ""
        try:
            # Clean up input
            clean_text = text.replace(" ", "")
            # Split into chunks of 8
            if len(clean_text) % 8 != 0:
                return "Error: Binary string length must be multiple of 8"

            chars = []
            for i in range(0, len(clean_text), 8):
                byte = clean_text[i:i + 8]
                chars.append(chr(int(byte, 2)))
            return "".join(chars)
        except ValueError as e:
            return f"Error: Invalid binary string ({e})"

    def unicode_escape(self, text: str) -> str:
        """Escapes non-ASCII characters to Unicode escape sequences."""
        if not text:
            return ""
        return text.encode("unicode_escape").decode("utf-8")

    def unicode_unescape(self, text: str) -> str:
        """Unescapes Unicode escape sequences."""
        if not text:
            return ""
        try:
            return text.encode("utf-8").decode("unicode_escape")
        except Exception as e:
            return f"Error: Invalid escape sequence ({e})"

    def leet_speak(self, text: str) -> str:
        """Converts text to basic Leet Speak (1337)."""
        if not text:
            return ""
        mapping = {
            'a': '4', 'b': '8', 'e': '3', 'g': '9', 'l': '1', 'o': '0', 's': '5', 't': '7', 'z': '2'
        }
        result = []
        for char in text:
            lower = char.lower()
            if lower in mapping:
                result.append(mapping[lower])
            else:
                result.append(char)
        return "".join(result)
