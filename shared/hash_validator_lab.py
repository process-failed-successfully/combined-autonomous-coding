"""
Hash Validator Lab
==================

Provides functionality to detect hash types and verify if an input matches a given hash.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


class HashValidatorManager:
    """Manages hash detection and verification."""

    HASH_LENGTHS = {
        32: ["md5"],
        40: ["sha1"],
        56: ["sha224", "sha3_224"],
        64: ["sha256", "sha3_256", "blake2s"],
        96: ["sha384", "sha3_384", "blake2b"],
        128: ["sha512", "sha3_512"]
    }

    def detect_hash_type(self, hash_value: str) -> List[str]:
        """Detects possible hash algorithms based on the length of the hex string."""
        hash_value = hash_value.strip().lower()

        # Check if it's a valid hex string
        try:
            int(hash_value, 16)
        except ValueError:
            return []

        length = len(hash_value)
        return self.HASH_LENGTHS.get(length, [])

    def verify_hash(self, input_text: str, expected_hash: str, algorithm: Optional[str] = None) -> Dict[str, Any]:
        """Verifies if the input text hashes to the expected hash."""
        expected_hash = expected_hash.strip().lower()
        input_bytes = input_text.encode('utf-8')

        algorithms_to_try = [algorithm.lower()] if algorithm else self.detect_hash_type(expected_hash)

        if not algorithms_to_try:
            return {
                "success": False,
                "error": "Could not detect hash algorithm, and none was provided.",
                "match": False
            }

        for algo in algorithms_to_try:
            try:
                h = hashlib.new(algo)
                h.update(input_bytes)
                if h.hexdigest() == expected_hash:
                    return {
                        "success": True,
                        "match": True,
                        "algorithm": algo
                    }
            except ValueError:
                # Unsupported algorithm by hashlib
                continue

        return {
            "success": True,
            "match": False,
            "error": "Input does not match the expected hash.",
            "tried_algorithms": algorithms_to_try
        }


def run_hash_validator_lab_logic(args):
    """CLI logic for hash-validator-lab."""
    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching Hash Validator Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-hash-validator")
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
        return

    manager = HashValidatorManager()

    if getattr(args, "action", None) == "detect":
        if not args.hash:
            print("Error: --hash is required for detect action.", file=sys.stderr)
            sys.exit(1)
            return

        algos = manager.detect_hash_type(args.hash)
        if algos:
            print(f"Possible algorithms for given hash length ({len(args.hash)} chars):")
            for algo in algos:
                print(f"  - {algo}")
            sys.exit(0)
        else:
            print("Could not detect any standard hash algorithm for this input.")
            sys.exit(1)

    elif getattr(args, "action", None) == "verify":
        if not args.hash:
            print("Error: --hash is required for verify action.", file=sys.stderr)
            sys.exit(1)
            return

        input_text = ""
        if getattr(args, "file", None):
            try:
                with open(args.file, "r") as f:
                    input_text = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        elif getattr(args, "text", None) is not None:
            input_text = args.text
        else:
            if not sys.stdin.isatty():
                input_text = sys.stdin.read()
            else:
                print("Error: Please provide input via --text, --file, or stdin.", file=sys.stderr)
                sys.exit(1)

        result = manager.verify_hash(input_text, args.hash, getattr(args, "algorithm", None))

        if result.get("match"):
            print(f"✅ Match found! Algorithm: {result['algorithm']}")
            sys.exit(0)
        else:
            print("❌ No match found.")
            if "tried_algorithms" in result:
                print(f"Tried algorithms: {', '.join(result['tried_algorithms'])}")
            if "error" in result and not result.get("success"):
                print(f"Error: {result['error']}")
            sys.exit(1)
    else:
        print("Unknown action or missing arguments.", file=sys.stderr)
        sys.exit(1)
