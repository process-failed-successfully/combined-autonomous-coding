import sys
import json
from typing import Dict, Union

class LevenshteinLabManager:
    """
    Manages Levenshtein distance calculations.
    """

    def distance(self, s1: str, s2: str) -> int:
        """
        Calculates the Levenshtein distance between two strings using dynamic programming.
        """
        if len(s1) < len(s2):
            return self.distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def similarity(self, s1: str, s2: str) -> float:
        """
        Calculates a similarity ratio between 0.0 and 1.0 based on the Levenshtein distance.
        """
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0

        dist = self.distance(s1, s2)
        return (max_len - dist) / max_len


def run_levenshtein_lab_logic(args):
    """CLI Entry point for Levenshtein Lab."""
    manager = LevenshteinLabManager()

    if args.action == "distance":
        try:
            dist = manager.distance(args.string1, args.string2)
            sim = manager.similarity(args.string1, args.string2)

            result = {
                "string1": args.string1,
                "string2": args.string2,
                "distance": dist,
                "similarity": round(sim, 4)
            }
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"Error calculating distance: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
