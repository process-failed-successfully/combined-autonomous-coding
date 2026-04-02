import argparse
import sys
from typing import Dict, Any

try:
    from mnemonic import Mnemonic
except ImportError:
    Mnemonic = None


class Bip39LabManager:
    """Manages BIP39 mnemonic phrase operations."""

    def __init__(self, language: str = "english"):
        if Mnemonic is None:
            raise RuntimeError("The 'mnemonic' library is not installed. Run 'pip install mnemonic'.")
        try:
            self.mnemo = Mnemonic(language)
        except Exception as e:
            raise ValueError(f"Language '{language}' is not supported by the mnemonic library. ({str(e)})")

    def generate(self, strength: int = 128) -> Dict[str, Any]:
        """Generates a new BIP39 mnemonic phrase.
        Strength is the number of bits of entropy. 128 = 12 words, 256 = 24 words.
        """
        if strength not in [128, 160, 192, 224, 256]:
            return {"success": False, "error": "Invalid strength. Must be 128, 160, 192, 224, or 256."}

        try:
            phrase = self.mnemo.generate(strength=strength)
            return {"success": True, "phrase": phrase}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate(self, phrase: str) -> Dict[str, Any]:
        """Validates a BIP39 mnemonic phrase."""
        try:
            is_valid = self.mnemo.check(phrase)
            return {"success": True, "valid": is_valid}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def to_seed(self, phrase: str, passphrase: str = "") -> Dict[str, Any]:
        """Converts a BIP39 mnemonic phrase to a binary seed and returns its hex representation."""
        # First validate the phrase, although mnemonic library doesn't strictly require it
        # it's good practice. We'll proceed even if check fails, but we can return the check status too.
        is_valid = self.mnemo.check(phrase)
        if not is_valid:
            # We can still generate a seed, but let's notify it's invalid.
            pass

        try:
            seed = self.mnemo.to_seed(phrase, passphrase=passphrase)
            return {"success": True, "seed_hex": seed.hex(), "valid_phrase": is_valid}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_bip39_lab_logic(args: argparse.Namespace) -> bool:
    """Entry point for the Bip39Lab CLI."""
    if Mnemonic is None:
        print("Error: The 'mnemonic' library is not installed.", file=sys.stderr)
        return False

    language = getattr(args, "language", "english")
    try:
        manager = Bip39LabManager(language=language)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    subcommand = getattr(args, "bip39_action", None)

    if subcommand == "generate":
        strength = getattr(args, "strength", 128)
        result = manager.generate(strength=strength)
        if result["success"]:
            print(result["phrase"])
            return True
        else:
            print(f"Error generating mnemonic: {result['error']}", file=sys.stderr)
            return False

    elif subcommand == "validate":
        phrase = getattr(args, "phrase", None)
        if not phrase:
            print("Error: --phrase is required for validate.", file=sys.stderr)
            return False
        result = manager.validate(phrase)
        if result["success"]:
            if result["valid"]:
                print("Phrase is VALID.")
                return True
            else:
                print("Phrase is INVALID.")
                return False
        else:
            print(f"Error validating mnemonic: {result['error']}", file=sys.stderr)
            return False

    elif subcommand == "seed":
        phrase = getattr(args, "phrase", None)
        if not phrase:
            print("Error: --phrase is required for seed generation.", file=sys.stderr)
            return False
        passphrase = getattr(args, "passphrase", "")
        result = manager.to_seed(phrase, passphrase=passphrase)
        if result["success"]:
            if not result["valid_phrase"]:
                print("Warning: The provided phrase is invalid, but a seed was generated anyway.", file=sys.stderr)
            print(result["seed_hex"])
            return True
        else:
            print(f"Error generating seed: {result['error']}", file=sys.stderr)
            return False

    else:
        print("Error: Invalid or missing subcommand for bip39-lab.", file=sys.stderr)
        return False
