import re
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class RegexGameLevel:
    name: str
    description: str
    positive_cases: List[str]
    negative_cases: List[str]

class RegexGameEngine:
    def validate(self, pattern: str, level: RegexGameLevel) -> Dict[str, Any]:
        """
        Validates a regex pattern against a level.
        Returns a dict with 'success' (bool), 'positive_results' (list), 'negative_results' (list).
        """
        results = {
            "success": False,
            "positive_results": [], # List of (case, passed)
            "negative_results": [], # List of (case, passed)
            "error": None
        }

        try:
            regex = re.compile(pattern)
        except re.error as e:
            results["error"] = str(e)
            return results

        all_passed = True

        for case in level.positive_cases:
            # We use fullmatch to encourage precise regexes in the game.
            matched = bool(regex.fullmatch(case))
            results["positive_results"].append((case, matched))
            if not matched:
                all_passed = False

        for case in level.negative_cases:
            matched = bool(regex.fullmatch(case))
            # Negative case passed if NOT matched
            passed = not matched
            results["negative_results"].append((case, passed))
            if not passed:
                all_passed = False

        results["success"] = all_passed
        return results

class RegexGameGenerator:
    def generate_levels(self) -> List[RegexGameLevel]:
        return [
            RegexGameLevel(
                name="Level 1: The Basics",
                description="Match exactly the word 'cat'.",
                positive_cases=["cat"],
                negative_cases=["dog", "category", "scat", "cats"]
            ),
            RegexGameLevel(
                name="Level 2: Digits",
                description="Match a string consisting of exactly 3 digits.",
                positive_cases=["123", "007", "999"],
                negative_cases=["12", "1234", "abc", "1a2"]
            ),
            RegexGameLevel(
                name="Level 3: Optional",
                description="Match 'color' or 'colour'.",
                positive_cases=["color", "colour"],
                negative_cases=["colouur", "colr", "colors"]
            ),
            RegexGameLevel(
                name="Level 4: Emails (Simple)",
                description="Match a simple email address (user@domain.com). No fancy validation needed, just alphanumeric + @ + alphanumeric + . + alphanumeric.",
                positive_cases=["test@example.com", "user123@gmail.com"],
                negative_cases=["test@example", "test.com", "@example.com"]
            ),
             RegexGameLevel(
                name="Level 5: Dates (YYYY-MM-DD)",
                description="Match dates in YYYY-MM-DD format.",
                positive_cases=["2023-01-01", "1999-12-31"],
                negative_cases=["2023/01/01", "01-01-2023", "2023-1-1"]
            )
        ]
