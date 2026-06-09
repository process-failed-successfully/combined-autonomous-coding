import sys
import json
from typing import Dict, List, Optional, Tuple

class CspLabManager:
    """Manages Content Security Policy parsing, generating, and validating."""

    # Common directives from CSP Level 3
    KNOWN_DIRECTIVES = {
        "child-src", "connect-src", "default-src", "font-src", "frame-src",
        "img-src", "manifest-src", "media-src", "object-src", "prefetch-src",
        "script-src", "script-src-elem", "script-src-attr", "style-src",
        "style-src-elem", "style-src-attr", "worker-src", "base-uri",
        "plugin-types", "sandbox", "form-action", "frame-ancestors",
        "navigate-to", "report-uri", "report-to", "block-all-mixed-content",
        "referrer", "require-sri-for", "require-trusted-types-for",
        "trusted-types", "upgrade-insecure-requests"
    }

    def parse(self, policy: str) -> Dict[str, List[str]]:
        """Parses a CSP string into a dictionary of directives and values."""
        if not policy:
            return {}

        result = {}
        # Directives are separated by semicolons
        directives = [d.strip() for d in policy.split(';') if d.strip()]

        for d in directives:
            parts = [p.strip() for p in d.split() if p.strip()]
            if not parts:
                continue
            name = parts[0].lower()
            values = parts[1:]
            result[name] = values

        return result

    def generate(self, parsed_policy: Dict[str, List[str]]) -> str:
        """Generates a CSP string from a dictionary of directives and values."""
        if not parsed_policy:
            return ""

        parts = []
        for name, values in parsed_policy.items():
            if values:
                parts.append(f"{name} {' '.join(values)}")
            else:
                parts.append(name)

        return "; ".join(parts)

    def validate(self, policy: str) -> Tuple[bool, List[str]]:
        """Validates a CSP string and returns a tuple of (is_valid, list_of_warnings)."""
        if not policy:
            return False, ["Empty policy."]

        parsed = self.parse(policy)
        warnings = []

        for name, values in parsed.items():
            if name not in self.KNOWN_DIRECTIVES:
                warnings.append(f"Unknown directive: '{name}'")

            # Some directives should usually have values
            if not values and name not in {"block-all-mixed-content", "upgrade-insecure-requests", "sandbox"}:
                warnings.append(f"Directive '{name}' has no values.")

            # Check for missing quotes on special keywords
            for val in values:
                lower_val = val.lower()
                if lower_val in {"self", "none", "unsafe-inline", "unsafe-eval", "strict-dynamic", "unsafe-hashes", "report-sample"} and not (val.startswith("'") and val.endswith("'")):
                    warnings.append(f"Keyword '{val}' in directive '{name}' should be enclosed in single quotes (e.g. '{lower_val}').")

        return len(warnings) == 0, warnings

def run_csp_lab_logic(args) -> bool:
    """CLI logic for CSP Lab."""
    manager = CspLabManager()

    if getattr(args, "action", None) == "tui":
        return True

    try:
        if args.action == "parse":
            parsed = manager.parse(args.policy)
            print(json.dumps(parsed, indent=2))
        elif args.action == "validate":
            is_valid, warnings = manager.validate(args.policy)
            if is_valid:
                print("✅ Policy is valid.")
            else:
                print("❌ Policy has issues:")
                for w in warnings:
                    print(f"  - {w}")
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
