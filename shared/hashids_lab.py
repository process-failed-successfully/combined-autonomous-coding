import argparse
import sys
from typing import List

try:
    from hashids import Hashids
    HAS_HASHIDS = True
except ImportError:
    HAS_HASHIDS = False

class HashidsLabManager:
    """Manages Hashids generation and decoding."""

    def __init__(self, salt: str = "", min_length: int = 0, alphabet: str = ""):
        if not HAS_HASHIDS:
            raise ImportError("hashids library not installed. Please install it using 'pip install hashids'.")

        kwargs = {"salt": salt, "min_length": min_length}
        if alphabet:
            kwargs["alphabet"] = alphabet

        try:
            self.hashids = Hashids(**kwargs)
        except ValueError as e:
            raise ValueError(f"Failed to initialize Hashids: {e}")

    def encode(self, numbers: List[int]) -> str:
        """Encodes a list of integers into a Hashid."""
        if not numbers:
             raise ValueError("Please provide at least one integer to encode.")
        for num in numbers:
            if num < 0:
                 raise ValueError("Hashids only supports positive integers.")
        return self.hashids.encode(*numbers)

    def decode(self, hashid: str) -> List[int]:
        """Decodes a Hashid back into a list of integers."""
        if not hashid:
             raise ValueError("Please provide a Hashid to decode.")
        return list(self.hashids.decode(hashid))


def run_hashids_lab_logic(args: argparse.Namespace) -> bool:
    """CLI Entry point for Hashids Lab."""

    if args.action == "tui":
        from shared.tui import AgentTUI
        from pathlib import Path
        print("Launching Hashids Lab TUI...")
        app = AgentTUI(project_dir=Path("."), start_tab="tab-hashids")
        app.run()
        sys.exit(0)

    try:
        manager = HashidsLabManager(salt=args.salt, min_length=args.min_length, alphabet=args.alphabet)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    if args.action == "encode":
        if not args.numbers:
             print("Error: Please provide integers to encode.", file=sys.stderr)
             return False

        try:
            encoded = manager.encode(args.numbers)
            print(encoded)
            return True
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "decode":
        if not args.hashid:
             print("Error: Please provide a hashid to decode.", file=sys.stderr)
             return False
        try:
            decoded = manager.decode(args.hashid)
            if not decoded:
                 print("Error: Could not decode Hashid. Check your salt and alphabet.", file=sys.stderr)
                 return False

            print(" ".join(map(str, decoded)))
            return True
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    return False
