from typing import Dict, Any
"""
Grok Lab
========

Provides utilities for parsing log lines using Grok patterns.
"""

import re
import sys


class GrokManager:
    """Manages Grok patterns and parsing."""

    def __init__(self):
        # A subset of standard grok patterns for convenience
        self.patterns = {
            "WORD": r"\w+",
            "INT": r"(?:[+-]?(?:[0-9]+))",
            "NUMBER": r"(?:(?:[+-]?(?:[0-9]+))(?:\.[0-9]+)?)",
            "SPACE": r"\s*",
            "NOTSPACE": r"\S+",
            "IPV4": r"(?<![0-9])(?:(?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})[.](?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})[.](?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2})[.](?:25[0-5]|2[0-4][0-9]|[0-1]?[0-9]{1,2}))(?![0-9])",
            "EMAILADDRESS": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "TIMESTAMP_ISO8601": r"%{YEAR}-%{MONTHNUM}-%{MONTHDAY}[T ]%{HOUR}:?%{MINUTE}(?::?%{SECOND})?%{ISO8601_TIMEZONE}?",
            "YEAR": r"\d{4}",
            "MONTHNUM": r"0[1-9]|1[0-2]",
            "MONTHDAY": r"(?:0[1-9])|(?:[12][0-9])|(?:3[01])",
            "HOUR": r"2[0123]|[01]?[0-9]",
            "MINUTE": r"[0-5][0-9]",
            "SECOND": r"(?:[0-5]?[0-9]|60)(?:[:.,][0-9]+)?",
            "ISO8601_TIMEZONE": r"(?:Z|[+-]%{HOUR}(?::?%{MINUTE}))",
            "LOGLEVEL": r"(?:DEBUG|INFO|NOTICE|WARN(?:ING)?|ERR(?:OR)?|CRIT(?:ICAL)?|FATAL|TRACE)",
            "COMMONAPACHELOG": r"%{IPV4:clientip} %{NOTSPACE:ident} %{NOTSPACE:auth} \[%{NOTSPACE:timestamp}\] \"%{WORD:verb} %{NOTSPACE:request} HTTP/%{NUMBER:httpversion}\" %{INT:response} %{INT:bytes}",
        }

    def add_pattern(self, name: str, pattern: str):
        self.patterns[name] = pattern

    def _build_regex(self, pattern: str) -> str:
        """Converts a Grok pattern into a regular Python regex string."""
        regex = pattern

        while True:
            # Match %{PATTERN:name} or %{PATTERN}
            m = re.search(r"%{([^}:]+)(?::([^}]+))?}", regex)
            if not m:
                break

            patt_name = m.group(1)
            cap_name = m.group(2)

            if patt_name not in self.patterns:
                raise ValueError(f"Pattern '{patt_name}' not found")

            patt_regex = self.patterns[patt_name]

            if cap_name:
                # Group names in python must be valid identifiers
                cap_name_safe = re.sub(r'[^a-zA-Z0-9_]', '_', cap_name)
                replacement = f"(?P<{cap_name_safe}>{patt_regex})"
            else:
                replacement = f"(?:{patt_regex})"

            regex = regex[:m.start()] + replacement + regex[m.end():]

        return regex

    def parse(self, pattern: str, text: str) -> Dict[str, str]:
        """Parses the text using the grok pattern and returns captured fields."""
        try:
            regex_str = self._build_regex(pattern)
            compiled = re.compile(regex_str)
            m = compiled.search(text)
            if m:
                return m.groupdict()
            return {}
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error parsing pattern: {e}")

    def list_patterns(self) -> Dict[str, str]:
        """Returns the dictionary of loaded patterns."""
        return self.patterns


def run_grok_lab_logic(args):
    """CLI logic for Grok Lab."""
    manager = GrokManager()

    if getattr(args, "action", None) == "patterns":
        print("--- Available Grok Patterns ---")
        for name, patt in sorted(manager.list_patterns().items()):
            print(f"{name}: {patt}")
        return True

    elif getattr(args, "action", None) == "parse":
        if not getattr(args, "pattern", None) or not getattr(args, "text", None):
            print("Error: --pattern and --text are required for 'parse'.", file=sys.stderr)
            return False

        try:
            result = manager.parse(args.pattern, args.text)
            if result:
                print("--- Parsed Fields ---")
                import json
                print(json.dumps(result, indent=2))
            else:
                print("No match found.")
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    return False
