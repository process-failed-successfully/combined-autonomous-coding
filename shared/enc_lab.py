"""
Encoding Lab
============

Utilities for common encoding/decoding operations:
- Base64
- URL
- HTML Entities
- Hex
- Rot13
"""

import sys
import base64
import urllib.parse
import html
import binascii
import codecs
from typing import Optional
from rich.console import Console

console = Console()

class EncLabManager:
    """Manages encoding and decoding operations."""

    def base64_process(self, text: str, decode: bool = False) -> str:
        """Encodes or decodes Base64 string."""
        if decode:
            try:
                # Add padding if missing
                padding = len(text) % 4
                if padding:
                    text += '=' * (4 - padding)
                return base64.b64decode(text).decode('utf-8')
            except Exception as e:
                raise ValueError(f"Invalid Base64 string: {e}")
        else:
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def url_process(self, text: str, decode: bool = False) -> str:
        """Encodes or decodes URL string."""
        if decode:
            return urllib.parse.unquote(text)
        else:
            return urllib.parse.quote(text)

    def html_process(self, text: str, decode: bool = False) -> str:
        """Encodes or decodes HTML entities."""
        if decode:
            return html.unescape(text)
        else:
            return html.escape(text)

    def hex_process(self, text: str, decode: bool = False) -> str:
        """Encodes string to hex or decodes hex to string."""
        if decode:
            try:
                # Remove spaces if any
                text = text.replace(" ", "")
                return bytes.fromhex(text).decode('utf-8')
            except Exception as e:
                raise ValueError(f"Invalid Hex string: {e}")
        else:
            return text.encode('utf-8').hex()

    def rot13_process(self, text: str) -> str:
        """Applies ROT13 transformation."""
        return codecs.encode(text, 'rot_13')


def run_enc_lab_logic(args) -> bool:
    """CLI handler for Encoding Lab."""
    manager = EncLabManager()

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

    text_input = get_input(args.text)
    if not text_input:
        console.print("[red]Error: Input text required (argument or stdin).[/red]")
        return False

    try:
        if args.action == "base64":
            result = manager.base64_process(text_input, decode=args.decode)
            print(result)

        elif args.action == "url":
            result = manager.url_process(text_input, decode=args.decode)
            print(result)

        elif args.action == "html":
            result = manager.html_process(text_input, decode=args.decode)
            print(result)

        elif args.action == "hex":
            result = manager.hex_process(text_input, decode=args.decode)
            print(result)

        elif args.action == "rot13":
            # rot13 is symmetric, so decode flag is ignored but accepted for consistency
            result = manager.rot13_process(text_input)
            print(result)

        return True

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False
