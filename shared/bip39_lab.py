import sys

try:
    from mnemonic import Mnemonic
    HAS_MNEMONIC = True
except ImportError:
    HAS_MNEMONIC = False


class Bip39LabManager:
    """Manages BIP39 operations (generate, validate, seed)."""

    def __init__(self, language: str = "english"):
        if not HAS_MNEMONIC:
            raise ImportError("mnemonic library is not installed. Please run: pip install mnemonic")
        self.mnemo = Mnemonic(language)

    def generate(self, strength: int = 128) -> str:
        """Generates a BIP39 mnemonic phrase.
        strength: 128 (12 words), 160 (15), 192 (18), 224 (21), 256 (24)
        """
        if strength not in [128, 160, 192, 224, 256]:
            raise ValueError("Strength must be one of: 128, 160, 192, 224, 256")
        return self.mnemo.generate(strength=strength)

    def validate(self, phrase: str) -> bool:
        """Validates a BIP39 mnemonic phrase."""
        return self.mnemo.check(phrase)

    def generate_seed(self, phrase: str, passphrase: str = "") -> bytes:
        """Generates a seed from a mnemonic phrase and an optional passphrase."""
        if not self.validate(phrase):
            raise ValueError("Invalid mnemonic phrase.")
        return self.mnemo.to_seed(phrase, passphrase)


def run_bip39_lab_logic(args) -> bool:
    """CLI handler for BIP39 Lab."""
    if not HAS_MNEMONIC:
        print("Error: mnemonic library is not installed.", file=sys.stderr)
        return False

    try:
        manager = Bip39LabManager(language=getattr(args, 'language', 'english'))

        if args.action == "generate":
            strength = getattr(args, 'strength', 128)
            phrase = manager.generate(strength=strength)
            print(phrase)
            return True

        elif args.action == "validate":
            if not args.phrase:
                print("Error: Phrase is required for validation.", file=sys.stderr)
                return False

            is_valid = manager.validate(args.phrase)
            if is_valid:
                print("✅ Valid BIP39 mnemonic phrase.")
                return True
            else:
                print("❌ Invalid BIP39 mnemonic phrase.", file=sys.stderr)
                return False

        elif args.action == "seed":
            if not args.phrase:
                print("Error: Phrase is required to generate seed.", file=sys.stderr)
                return False

            passphrase = getattr(args, 'passphrase', "")
            try:
                seed = manager.generate_seed(args.phrase, passphrase=passphrase)
                print(seed.hex())
                return True
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return False

        elif args.action == "tui":
            # TUI handled in main.py routing or here
            from shared.tui import AgentTUI
            import asyncio
            print("Launching BIP39 Lab TUI...")
            app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-bip39")
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                asyncio.ensure_future(app.run_async())
            else:
                app.run()
            return True

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
