import re
from typing import Dict, Any, List

class MaskLabManager:
    """Manages masking of Personally Identifiable Information (PII)."""

    PII_PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "ipv4": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    }

    def mask_text(self, text: str, rules: List[str] = None, mask_char: str = '*') -> str:
        """
        Masks requested PII in the text.

        Args:
            text: The text to mask.
            rules: List of PII types to mask (e.g., ['email', 'phone']). If None, masks all.
            mask_char: The character to replace PII with.

        Returns:
            The masked text.
        """
        if not text:
            return text

        if rules is None:
            rules = list(self.PII_PATTERNS.keys())

        masked_text = text
        for rule in rules:
            if rule in self.PII_PATTERNS:
                pattern = self.PII_PATTERNS[rule]

                # Special handling for different types to keep some context
                if rule == "email":
                    masked_text = re.sub(pattern, self._mask_email, masked_text)
                elif rule == "credit_card":
                    masked_text = re.sub(pattern, lambda m: self._mask_preserve_last_n(m, 4, mask_char), masked_text)
                else:
                    masked_text = re.sub(pattern, lambda m: mask_char * len(m.group(0)), masked_text)

        return masked_text

    def _mask_email(self, match) -> str:
        email = match.group(0)
        parts = email.split('@')
        if len(parts) != 2:
            return '*' * len(email)

        local, domain = parts
        if len(local) > 2:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        else:
            masked_local = '*' * len(local)

        return f"{masked_local}@{domain}"

    def _mask_preserve_last_n(self, match, n: int, mask_char: str) -> str:
        matched_str = match.group(0)
        # Count only digits
        digits_count = sum(1 for c in matched_str if c.isdigit())

        if digits_count <= n:
            return mask_char * len(matched_str)

        masked_result = ""
        digits_seen = 0
        for char in reversed(matched_str):
            if char.isdigit():
                if digits_seen < n:
                    masked_result = char + masked_result
                else:
                    masked_result = mask_char + masked_result
                digits_seen += 1
            else:
                masked_result = char + masked_result

        return masked_result


def run_mask_lab_logic(args) -> bool:
    """CLI logic for mask-lab"""
    import sys
    from shared.cli_utils import read_input

    # Need to handle standard CLI inputs
    text = args.text
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read()

    if not text:
        print("Please provide text using --text or stdin.")
        return False

    manager = MaskLabManager()

    rules = []
    if args.email: rules.append("email")
    if args.phone: rules.append("phone")
    if args.credit_card: rules.append("credit_card")
    if args.ssn: rules.append("ssn")
    if args.ipv4: rules.append("ipv4")

    if not rules:
        rules = None # Default to all

    masked = manager.mask_text(text, rules=rules, mask_char=args.mask_char)
    print(masked)
    return True
