import sys
import json
import argparse
from typing import Dict, Any, Optional
from mnemonic import Mnemonic

class Bip39LabManager:
    """
    Manages BIP39 Mnemonic operations using the python-mnemonic library.
    """
    def __init__(self, language: str = 'english'):
        self.language = language
        self.mnemo = Mnemonic(language)

    def generate(self, words: int = 12) -> Dict[str, Any]:
        """
        Generates a new BIP39 mnemonic phrase.
        Valid word counts: 12, 15, 18, 21, 24.
        """
        valid_words_to_strength = {
            12: 128,
            15: 160,
            18: 192,
            21: 224,
            24: 256
        }

        if words not in valid_words_to_strength:
            return {"success": False, "error": "Invalid word count. Must be 12, 15, 18, 21, or 24."}

        strength = valid_words_to_strength[words]
        try:
            phrase = self.mnemo.generate(strength=strength)
            return {"success": True, "phrase": phrase}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate(self, phrase: str) -> Dict[str, Any]:
        """
        Validates a BIP39 mnemonic phrase.
        """
        try:
            is_valid = self.mnemo.check(phrase)
            return {"success": True, "is_valid": is_valid}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def to_seed(self, phrase: str, passphrase: str = '') -> Dict[str, Any]:
        """
        Converts a mnemonic phrase to a binary seed (returned as hex).
        """
        try:
            if not self.mnemo.check(phrase):
                 return {"success": False, "error": "Invalid mnemonic phrase."}

            seed = self.mnemo.to_seed(phrase, passphrase=passphrase)
            seed_hex = seed.hex()
            return {"success": True, "seed_hex": seed_hex}
        except Exception as e:
             return {"success": False, "error": str(e)}


def run_bip39_lab_logic(args: argparse.Namespace) -> bool:
    """
    CLI handler for BIP39 Lab.
    """
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching BIP39 Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-bip39")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return True

    manager = Bip39LabManager()

    if args.action == "generate":
        words = getattr(args, "words", 12)
        result = manager.generate(words=words)
        if result["success"]:
            print(json.dumps({"phrase": result["phrase"]}, indent=2))
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False

    elif args.action == "validate":
        phrase = getattr(args, "phrase", None)
        if not phrase:
             print("Error: --phrase is required for validate.", file=sys.stderr)
             return False

        result = manager.validate(phrase)
        if result["success"]:
             print(json.dumps({"valid": result["is_valid"]}, indent=2))
             return True
        else:
             print(f"Error: {result['error']}", file=sys.stderr)
             return False

    elif args.action == "seed":
        phrase = getattr(args, "phrase", None)
        passphrase = getattr(args, "passphrase", "")

        if not phrase:
             print("Error: --phrase is required for seed.", file=sys.stderr)
             return False

        result = manager.to_seed(phrase, passphrase)
        if result["success"]:
            print(json.dumps({"seed": result["seed_hex"]}, indent=2))
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False
    else:
        print(f"Error: Unknown action '{args.action}'", file=sys.stderr)
        return False
