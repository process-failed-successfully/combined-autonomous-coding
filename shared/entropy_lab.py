import argparse
import math
import sys
from collections import Counter
from typing import Dict, Any, Union

class EntropyLabManager:
    """Manages Entropy calculations and analysis for data."""

    def calculate_entropy(self, data: bytes) -> float:
        """Calculates the Shannon entropy of the given byte data."""
        if not data:
            return 0.0
        length = len(data)
        counts = Counter(data)
        entropy = -sum((count / length) * math.log2(count / length) for count in counts.values())
        return entropy

    def analyze_data(self, data: bytes) -> Dict[str, Any]:
        """Analyzes data and provides entropy and heuristics."""
        entropy = self.calculate_entropy(data)
        length = len(data)

        # Simple heuristics based on entropy and length
        if length == 0:
            assessment = "Empty data"
        elif entropy < 3.0:
            assessment = "Low entropy (highly repetitive or simple text)"
        elif entropy < 5.0:
            assessment = "Moderate entropy (typical English text or simple code)"
        elif entropy < 7.0:
            assessment = "High entropy (complex text, some compressed data)"
        elif entropy >= 7.5:
            assessment = "Very high entropy (likely compressed, encrypted, or random data)"
        else:
            assessment = "High entropy"

        return {
            "entropy": entropy,
            "length": length,
            "assessment": assessment
        }


def run_entropy_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Entropy Lab."""
    manager = EntropyLabManager()

    data = None
    if getattr(args, "text", None) is not None:
        data = args.text.encode("utf-8")
    elif getattr(args, "file", None) is not None:
        try:
            with open(args.file, "rb") as f:
                data = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif not sys.stdin.isatty():
        # Read from pipe
        data = sys.stdin.buffer.read()

    if data is None:
        print("Error: Must provide --text, --file, or pipe data to stdin.", file=sys.stderr)
        return False

    result = manager.analyze_data(data)
    print(f"Size: {result['length']} bytes")
    print(f"Entropy: {result['entropy']:.4f} bits per byte")
    print(f"Assessment: {result['assessment']}")

    return True
