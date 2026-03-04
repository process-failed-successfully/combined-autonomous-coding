import sys
from typing import List
import tiktoken


class TokenLabManager:
    """Manager for token counting and text tokenization."""

    def __init__(self):
        pass

    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        """Counts the number of tokens in a string using the specified model's encoding."""
        if not text:
            return 0
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base if model is unknown
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def count_tokens_by_encoding(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Counts tokens using a specific encoding name."""
        if not text:
            return 0
        try:
            encoding = tiktoken.get_encoding(encoding_name)
        except ValueError:
            return 0
        return len(encoding.encode(text))

    def get_tokens(self, text: str, model: str = "gpt-4o") -> List[int]:
        """Returns the actual token integers for a given text."""
        if not text:
            return []
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode(text)

    def decode_tokens(self, tokens: List[int], model: str = "gpt-4o") -> str:
        """Decodes a list of token integers back to a string."""
        if not tokens:
            return ""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.decode(tokens)


def run_token_lab_logic(args):
    """CLI entry point for Token Lab."""
    manager = TokenLabManager()

    text = ""
    if hasattr(args, "text") and args.text:
        text = args.text
    elif hasattr(args, "file") and args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Try stdin
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("Error: No text provided via --text, --file, or stdin.", file=sys.stderr)
            sys.exit(1)

    model = getattr(args, "model", "gpt-4o")
    encoding_name = getattr(args, "encoding", None)

    if args.action == "count":
        if encoding_name:
            count = manager.count_tokens_by_encoding(text, encoding_name)
            print(f"Tokens ({encoding_name}): {count}")
        else:
            count = manager.count_tokens(text, model)
            print(f"Tokens ({model}): {count}")
    elif args.action == "tokenize":
        tokens = manager.get_tokens(text, model)
        print(f"Tokens: {tokens}")
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
