import argparse
import sys
import nanoid

class NanoIDLabManager:
    @staticmethod
    def generate_nanoid(size: int = 21, alphabet: str = None, count: int = 1) -> list[str]:
        """Generates one or more NanoIDs."""
        results = []
        for _ in range(count):
            if alphabet:
                results.append(nanoid.generate(alphabet=alphabet, size=size))
            else:
                results.append(nanoid.generate(size=size))
        return results

    @staticmethod
    def validate_nanoid(nanoid_str: str, size: int = 21, alphabet: str = None) -> bool:
        """Validates if a given string conforms to NanoID parameters."""
        if len(nanoid_str) != size:
            return False

        # nanoid library's default alphabet
        default_alphabet = '_-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        valid_chars = set(alphabet) if alphabet else set(default_alphabet)

        return all(c in valid_chars for c in nanoid_str)

def run_nanoid_lab_logic(args):
    """Entry point for NanoID Lab CLI."""
    manager = NanoIDLabManager()

    if args.action == "generate":
        try:
            ids = manager.generate_nanoid(
                size=args.size,
                alphabet=args.alphabet,
                count=args.count
            )
            for nid in ids:
                print(nid)
        except Exception as e:
            print(f"Error generating NanoID: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        if not args.nanoid:
            print("Error: --nanoid is required for validation.", file=sys.stderr)
            sys.exit(1)

        is_valid = manager.validate_nanoid(
            nanoid_str=args.nanoid,
            size=args.size,
            alphabet=args.alphabet
        )

        if is_valid:
            print(f"✅ '{args.nanoid}' is a valid NanoID.")
        else:
            print(f"❌ '{args.nanoid}' is NOT a valid NanoID.")
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
