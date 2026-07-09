import argparse
import sys
import json
from typing import Dict, Any, List, Optional
try:
    from pygrok import Grok
except ImportError:
    Grok = None


class GrokManager:
    """
    Manages Grok pattern parsing and extraction.
    """

    def parse(self, pattern: str, text: str) -> Dict[str, Any]:
        """
        Parses text against a Grok pattern and returns the extracted fields.
        """
        if Grok is None:
            return {"success": False, "error": "pygrok library is not installed"}

        try:
            grok = Grok(pattern)
            match = grok.match(text)

            if match is None:
                return {"success": False, "error": "Pattern did not match the input text."}

            return {"success": True, "match": match}
        except Exception as e:
            return {"success": False, "error": f"Error parsing Grok pattern: {e}"}

    def get_patterns(self) -> List[str]:
        """
        Returns a list of some common Grok patterns for reference.
        """
        return [
            "WORD",
            "NUMBER",
            "IP",
            "IPORHOST",
            "URI",
            "URIPATHPARAM",
            "TIMESTAMP_ISO8601",
            "SYSLOGTIMESTAMP",
            "EMAILADDRESS",
            "UUID",
            "MAC",
            "LOGLEVEL",
            "QS",
            "SPACE",
            "DATA",
            "GREEDYDATA"
        ]


def run_grok_lab_logic(args: argparse.Namespace) -> bool:
    """
    CLI handler for Grok Lab.
    """
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Grok Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-grok")
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
        return True

    manager = GrokManager()

    if getattr(args, "action", None) == "parse":
        if not getattr(args, "pattern", None) or not getattr(args, "text", None):
            print("Error: 'parse' action requires --pattern and --text arguments.", file=sys.stderr)
            return False

        result = manager.parse(args.pattern, args.text)
        if result["success"]:
            print(json.dumps(result["match"], indent=2))
            return True
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "patterns":
        patterns = manager.get_patterns()
        print("Common Grok Patterns:")
        for pattern in patterns:
            print(f"  - %{{{pattern}}}")
        return True

    else:
        print("Error: Invalid action. Use 'parse', 'patterns', or '--tui'.", file=sys.stderr)
        return False
