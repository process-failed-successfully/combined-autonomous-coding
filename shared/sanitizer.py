import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

class Sanitizer:
    """
    Sanitizes PII (Personally Identifiable Information) from text and files.
    Uses deterministic replacement to ensure consistency (e.g., same email mapped to same fake email).
    """

    PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "IPV4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "PHONE": r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        # Simple Credit Card (16 digits, possibly grouped)
        "CREDIT_CARD": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
    }

    def __init__(self, salt: str = "sanitizer_salt"):
        self.salt = salt
        # Cache for consistent replacement within a session if needed,
        # but we rely on hash for consistency across sessions too.
        self.cache: Dict[str, str] = {}

    def _get_hash(self, value: str) -> str:
        """Returns a short hash of the value."""
        return hashlib.sha256((value + self.salt).encode("utf-8")).hexdigest()[:8]

    def _replace_email(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        return f"user_{h}@sanitized.com"

    def _replace_ipv4(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        # Map hash to 10.x.x.x
        # Take first 3 bytes of hash for octets
        b = bytes.fromhex(h)
        return f"10.{b[0]}.{b[1]}.{b[2]}"

    def _replace_phone(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        # Generate 555-xxxx
        nums = int(h, 16) % 10000
        return f"555-01{nums:02d}" # 555-01xx is reserved for fiction

    def _replace_ssn(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        nums = int(h, 16) % 10000
        return f"000-00-{nums:04d}"

    def _replace_cc(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        nums = int(h, 16) % 10000
        return f"4000 0000 0000 {nums:04d}"

    def _replace_generic(self, match: re.Match) -> str:
        original = match.group(0)
        h = self._get_hash(original)
        return f"REDACTED_{h}"

    def sanitize_text(self, text: str) -> str:
        """Sanitizes text by replacing detected PII."""

        # We apply replacements sequentially.
        # Note: Order matters. e.g. Email might contain numbers resembling phone/ip if not careful.
        # But regexes above are relatively distinct.

        # Email
        text = re.sub(self.PATTERNS["EMAIL"], self._replace_email, text)

        # IPv4
        text = re.sub(self.PATTERNS["IPV4"], self._replace_ipv4, text)

        # Credit Card
        text = re.sub(self.PATTERNS["CREDIT_CARD"], self._replace_cc, text)

        # SSN
        text = re.sub(self.PATTERNS["SSN"], self._replace_ssn, text)

        # Phone
        text = re.sub(self.PATTERNS["PHONE"], self._replace_phone, text)

        return text

    def sanitize_file(self, input_path: Path, output_path: Path = None, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Sanitizes a file.
        Returns (changed, message).
        """
        input_path = input_path.resolve()
        if not input_path.exists():
            return False, f"File not found: {input_path}"

        try:
            content = input_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return False, f"Error reading file: {e}"

        sanitized = self.sanitize_text(content)

        if sanitized == content:
            return False, "No PII found."

        if dry_run:
            return True, "PII found (dry-run)."

        if output_path:
            try:
                output_path.write_text(sanitized, encoding="utf-8")
                return True, f"Sanitized content saved to {output_path}"
            except Exception as e:
                return False, f"Error writing to output: {e}"
        else:
            # Overwrite
            try:
                input_path.write_text(sanitized, encoding="utf-8")
                return True, f"Sanitized {input_path}"
            except Exception as e:
                return False, f"Error overwriting file: {e}"

    def check_text(self, text: str) -> List[str]:
        """Returns a list of detected PII types in the text."""
        detected = []
        for name, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                detected.append(name)
        return detected
