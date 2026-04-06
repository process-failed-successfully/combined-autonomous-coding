"""
Magic Decode Lab
================

Automatically attempts to decode an opaque string using various common formats:
- Base64
- URL Encoding
- Hex
- Binary
- Octal
- HTML Entities
- JWT (JSON Web Token)
- JSON
- Unix Timestamp
- ROT13
"""

import sys
import base64
import urllib.parse
import html
import binascii
import codecs
import json
from datetime import datetime
from rich.console import Console
from shared.jwt_lab import JWTManager

console = Console()

class MagicDecodeManager:
    """Attempts to decode a string automatically using multiple methods."""

    def decode(self, text: str) -> dict:
        """Tries multiple decoding methods and returns successful ones."""
        results = {}
        text = text.strip()

        if not text:
            return results

        def is_mostly_printable(s: str) -> bool:
            """Ensure decoded string isn't just binary garbage that happened to decode as UTF-8."""
            if not s:
                return False
            printable_count = sum(1 for c in s if c.isprintable() or c in '\n\r\t')
            return (printable_count / len(s)) > 0.9

        # 1. Base64
        try:
            # Check if it looks like base64 (only valid chars and correct length/padding)
            # Remove any trailing newlines
            b64_text = text.replace('\n', '').replace('\r', '')

            # Simple heuristic: must be at least 4 chars or divisible by 4, etc.
            # but standard b64decode just ignores some stuff, so let's be strict.
            if len(b64_text) % 4 == 0 or b64_text.endswith('='):
                # We need to pad to multiple of 4
                padding = len(b64_text) % 4
                if padding:
                    b64_text += '=' * (4 - padding)
                decoded = base64.b64decode(b64_text, validate=True).decode('utf-8')
                if decoded != text and is_mostly_printable(decoded):
                    results["Base64"] = decoded
        except Exception:
            pass

        # Try Base64 URL safe
        try:
            b64url_text = text.replace('\n', '').replace('\r', '')
            padding = len(b64url_text) % 4
            if padding:
                b64url_text += '=' * (4 - padding)
            decoded = base64.urlsafe_b64decode(b64url_text).decode('utf-8')
            if decoded != text and is_mostly_printable(decoded) and "Base64" not in results:
                results["Base64 URL-Safe"] = decoded
        except Exception:
            pass

        # 2. URL Encoding
        try:
            if '%' in text:
                decoded = urllib.parse.unquote(text)
                if decoded != text:
                    results["URL Encoded"] = decoded
        except Exception:
            pass

        # 3. HTML Entities
        try:
            if '&' in text and ';' in text:
                decoded = html.unescape(text)
                if decoded != text:
                    results["HTML Entities"] = decoded
        except Exception:
            pass

        # 4. Hex
        try:
            # Hex string typically has even length
            hex_text = text.replace(' ', '').replace('\n', '').replace('0x', '')
            if len(hex_text) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in hex_text):
                decoded = bytes.fromhex(hex_text).decode('utf-8')
                if decoded != text and is_mostly_printable(decoded):
                    results["Hex"] = decoded
        except Exception:
            pass

        # 5. JWT
        try:
            parts = text.split('.')
            if len(parts) == 3:
                decoded = JWTManager.decode_token(text)
                results["JWT"] = json.dumps(decoded, indent=2)
        except Exception:
            pass

        # 6. JSON
        try:
            if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
                parsed = json.loads(text)
                formatted = json.dumps(parsed, indent=2)
                if formatted != text:
                    results["JSON"] = formatted
        except Exception:
            pass

        # 7. Unix Timestamp
        try:
            from datetime import timezone
            if text.isdigit() and len(text) >= 9 and len(text) <= 13:
                ts = int(text)
                if len(text) > 10:  # Assume milliseconds
                    ts = ts / 1000.0
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                results["Unix Timestamp"] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except Exception:
            pass

        # 8. ROT13
        try:
            if any(c.isalpha() for c in text):
                decoded = codecs.encode(text, 'rot_13')
                # ROT13 is symmetric and always changes alpha chars.
                results["ROT13"] = decoded
        except Exception:
            pass

        # 9. Binary
        try:
            bin_text = text.replace(' ', '').replace('\n', '')
            if all(c in '01' for c in bin_text) and len(bin_text) % 8 == 0 and len(bin_text) > 0:
                chars = []
                for i in range(0, len(bin_text), 8):
                    byte = bin_text[i:i+8]
                    chars.append(chr(int(byte, 2)))
                decoded = ''.join(chars)
                if is_mostly_printable(decoded):
                    results["Binary"] = decoded
        except Exception:
            pass

        # 10. Octal
        try:
            # We want to check spaces and numbers, so don't completely strip spaces for splitting if they exist.
            octal_text = text.replace('\n', '')
            if all(c in '01234567 ' for c in octal_text) and any(c.isdigit() for c in octal_text):
                parts = octal_text.split()
                if not parts or len(parts) == 1:
                    # Try chunks of 3 if no spaces
                    octal_text = octal_text.replace(' ', '')
                    parts = [octal_text[i:i+3] for i in range(0, len(octal_text), 3)]
                chars = []
                for p in parts:
                    chars.append(chr(int(p, 8)))
                decoded = ''.join(chars)
                if is_mostly_printable(decoded) and decoded != text:
                    results["Octal"] = decoded
        except Exception:
            pass

        # We can also clean up ROT13. ROT13 will *always* trigger if there are alpha characters,
        # but if it doesn't match a valid decoding or isn't intended to be ROT13, it might just be noise.
        # However, since that's what magic decode is for, we keep it but maybe we only return it
        # if the decoded text looks meaningful, or just leave it.

        return results

def run_magic_decode_lab_logic(args) -> bool:
    """CLI handler for Magic Decode Lab."""
    manager = MagicDecodeManager()

    def get_input(arg_val):
        if arg_val:
            return arg_val
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read().strip()
            except Exception:
                pass
        return None

    text_input = get_input(args.text)
    if not text_input:
        console.print("[red]Error: Input text required (via --text or stdin).[/red]")
        return False

    results = manager.decode(text_input)

    if not results:
        console.print("[yellow]No decodings found. The string might not be in a recognized format or is just plain text.[/yellow]")
        return True

    console.print(f"[bold cyan]Magic Decode Results:[/bold cyan]\n")
    for format_name, decoded_val in results.items():
        console.print(f"[bold green]--- {format_name} ---[/bold green]")
        console.print(decoded_val)
        console.print("")

    return True
