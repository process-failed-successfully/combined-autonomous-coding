import json
import sys
import re
from typing import Dict, Any, Optional

class GrokManager:
    """Manages Grok pattern parsing and extraction."""

    # A collection of standard baseline Grok patterns.
    # In a full implementation, this could be loaded from files like logstash does.
    DEFAULT_PATTERNS = {
        "WORD": r"\b\w+\b",
        "NUMBER": r"(?:[+-]?(?:[0-9]+))(?:\.[0-9]+)?",
        "INT": r"(?:[+-]?(?:[0-9]+))",
        "IP": r"(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        "IPV4": r"(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        "IPV6": r"(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}",
        "MAC": r"(?:[A-Fa-f0-9]{2}[:-]){5}[A-Fa-f0-9]{2}",
        "TIMESTAMP_ISO8601": r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?",
        "SPACE": r"\s*",
        "NOTSPACE": r"\S+",
        "DATA": r".*?",
        "GREEDYDATA": r".*",
        "UUID": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        "URIPROTO": r"[A-Za-z]+(\+[A-Za-z+]+)?",
        "URIHOST": r"[A-Za-z0-9\-._~%]+",
        "URIPATH": r"/(?:[A-Za-z0-9\-._~%!$&'()*+,;=:@/]*)?",
        "EMAILADDRESS": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "LOGLEVEL": r"(?:DEBUG|INFO|NOTICE|WARNING|WARN|ERROR|CRIT|CRITICAL|FATAL|SEVERE|TRACE)",
        "MONTH": r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)",
        "DAY": r"(?:Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)",
        "SYSLOGTIMESTAMP": r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
    }

    def __init__(self, custom_patterns: Optional[Dict[str, str]] = None):
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)

    def compile(self, grok_pattern: str) -> re.Pattern:
        """
        Translates a Grok pattern into a regular Python regex.
        Supports %{PATTERN} and %{PATTERN:name}.
        Recursively resolves patterns up to a certain depth.
        """
        regex = grok_pattern
        max_iterations = 50  # Prevent infinite loops if patterns refer to themselves

        # Regex to find %{PATTERN} or %{PATTERN:name}
        grok_regex = re.compile(r"%\{(?P<pattern>[A-Z0-9_]+)(?::(?P<name>[a-zA-Z0-9_]+))?\}")

        for _ in range(max_iterations):
            match = grok_regex.search(regex)
            if not match:
                break

            pattern_name = match.group("pattern")
            capture_name = match.group("name")

            if pattern_name not in self.patterns:
                raise ValueError(f"Unknown pattern: {pattern_name}")

            replacement = self.patterns[pattern_name]

            if capture_name:
                # Wrap with named capture group
                replacement = f"(?P<{capture_name}>{replacement})"
            else:
                # Wrap in non-capturing group to preserve precedence
                replacement = f"(?:{replacement})"

            # Replace just this one match
            regex = regex[:match.start()] + replacement + regex[match.end():]

        if grok_regex.search(regex):
            raise ValueError("Max pattern recursion reached or unresolved patterns remaining.")

        try:
            return re.compile(regex)
        except re.error as e:
            raise ValueError(f"Generated invalid regex: {e}")

    def parse(self, grok_pattern: str, text: str) -> Dict[str, Any]:
        """
        Parses text using the specified Grok pattern.
        Returns a dictionary of matched fields.
        """
        try:
            compiled = self.compile(grok_pattern)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        match = compiled.search(text)
        if not match:
            return {"success": False, "error": "No match found"}

        return {
            "success": True,
            "fields": match.groupdict()
        }

def run_grok_lab_logic(args):
    """
    CLI handler for Grok Lab.
    """
    manager = GrokManager()

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        import asyncio
        from pathlib import Path
        print("Launching Grok Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-grok-lab")
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

    if not hasattr(args, "action"):
        print("Error: Action required.", file=sys.stderr)
        sys.exit(1)

    if args.action == "parse":
        result = manager.parse(args.pattern, args.text)
        if args.json:
            print(json.dumps(result, indent=2))
        elif result["success"]:
            print("✅ Match found!")
            for k, v in result["fields"].items():
                print(f"  {k}: {v}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    elif args.action == "patterns":
        if args.json:
            print(json.dumps(manager.patterns, indent=2))
        else:
            print("--- Available Grok Patterns ---")
            for k, v in sorted(manager.patterns.items()):
                print(f"{k}: {v}")

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
