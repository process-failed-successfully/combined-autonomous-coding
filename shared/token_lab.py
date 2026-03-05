import argparse
import sys
import tiktoken
from typing import Dict, Any


class TokenLabManager:
    """Manager for tokenizing text using tiktoken."""

    def __init__(self, model: str = "cl100k_base"):
        self.model = model
        try:
            self.encoding = tiktoken.get_encoding(self.model)
        except Exception as e:
            self.encoding = None
            self.error = str(e)

    def count_tokens(self, text: str) -> Dict[str, Any]:
        """Counts the number of tokens in a given text."""
        if not self.encoding:
            return {"success": False, "error": f"Failed to load encoding: {self.error}"}

        try:
            tokens = self.encoding.encode(text)
            return {"success": True, "count": len(tokens), "tokens": tokens}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def encode(self, text: str) -> Dict[str, Any]:
        """Encodes text to a list of tokens."""
        if not self.encoding:
            return {"success": False, "error": f"Failed to load encoding: {self.error}"}

        try:
            tokens = self.encoding.encode(text)
            return {"success": True, "tokens": tokens}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def decode(self, tokens: list[int]) -> Dict[str, Any]:
        """Decodes a list of tokens back to text."""
        if not self.encoding:
            return {"success": False, "error": f"Failed to load encoding: {self.error}"}

        try:
            text = self.encoding.decode(tokens)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_token_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for token lab."""
    manager = TokenLabManager(model=getattr(args, 'encoding', 'cl100k_base'))

    if args.action == "count":
        if not args.text:
            print("Error: --text is required for 'count' action.", file=sys.stderr)
            return False

        result = manager.count_tokens(args.text)
        if result["success"]:
            print(f"Token count: {result['count']}")
            if getattr(args, 'verbose', False):
                print(f"Tokens: {result['tokens']}")
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False

    elif args.action == "encode":
        if not args.text:
            print("Error: --text is required for 'encode' action.", file=sys.stderr)
            return False

        result = manager.encode(args.text)
        if result["success"]:
            print(f"Encoded tokens: {result['tokens']}")
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False

    elif args.action == "decode":
        if not getattr(args, 'tokens', None):
            print("Error: --tokens (comma-separated integers) is required for 'decode' action.", file=sys.stderr)
            return False

        try:
            tokens = [int(t.strip()) for t in args.tokens.split(",")]
        except ValueError:
            print("Error: --tokens must be a comma-separated list of integers.", file=sys.stderr)
            return False

        result = manager.decode(tokens)
        if result["success"]:
            print(f"Decoded text: {result['text']}")
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False

    return False
