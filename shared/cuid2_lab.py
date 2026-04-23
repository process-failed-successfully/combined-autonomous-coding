import sys
from typing import List
import argparse

# Try to import cuid2, provide fallback for CI/CD or environments without it
try:
    from cuid2 import Cuid
    HAS_CUID2 = True
except ImportError:
    HAS_CUID2 = False


class Cuid2LabManager:
    """Manages CUID2 operations."""

    def __init__(self):
        if not HAS_CUID2:
            raise ImportError("cuid2 library not installed. Please install it using 'pip install cuid2'.")

    def generate(self, count: int = 1, length: int = 24) -> List[str]:
        """Generates a list of CUID2s with the specified length."""
        cuid_generator = Cuid(length=length)
        return [cuid_generator.generate() for _ in range(count)]


def run_cuid2_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for CUID2 Lab."""

    if args.action == "tui":
        try:
            from shared.tui import AgentTUI
            from pathlib import Path
            app = AgentTUI(project_dir=Path("."), start_tab="tab-cuid2")
            app.run()
            return True
        except ImportError as e:
             print(f"Error launching TUI: {e}", file=sys.stderr)
             return False

    try:
        manager = Cuid2LabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "generate":
        try:
            count = getattr(args, "count", 1)
            length = getattr(args, "length", 24)

            results = manager.generate(count=count, length=length)
            for res in results:
                print(res)
            return True
        except Exception as e:
            print(f"Error generating CUID2: {e}", file=sys.stderr)
            sys.exit(1)

    return False
