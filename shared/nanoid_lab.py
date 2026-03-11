import sys
from typing import List, Optional
from nanoid import generate as generate_nanoid

class NanoIDLabManager:
    """Manages NanoID operations (generation, custom alphabet, sizing)."""

    def generate(self, count: int = 1, size: int = 21, alphabet: Optional[str] = None) -> List[str]:
        """Generates NanoIDs."""
        results = []
        for _ in range(count):
            if alphabet:
                results.append(generate_nanoid(alphabet, size))
            else:
                results.append(generate_nanoid(size=size))
        return results


def run_nanoid_lab_logic(args):
    """CLI handler for NanoID Lab."""
    manager = NanoIDLabManager()

    if args.action in ["generate", "gen"]:
        try:
            results = manager.generate(count=args.count, size=args.size, alphabet=args.alphabet)
            for res in results:
                print(res)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "bulk":
        try:
            results = manager.generate(count=args.count, size=args.size, alphabet=args.alphabet)
            for res in results:
                print(res)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
