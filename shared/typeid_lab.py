import sys
import argparse
from typing import List, Dict, Any

try:
    from typeid import TypeID
    HAS_TYPEID = True
except ImportError:
    HAS_TYPEID = False

class TypeIDLabManager:
    """Manages TypeID operations (generation, parsing)."""

    def __init__(self):
        if not HAS_TYPEID:
            raise ImportError("typeid-python library not installed. Please install it using 'pip install typeid-python'.")

    def generate(self, prefix: str, count: int = 1) -> List[str]:
        """Generates a list of TypeIDs for a given prefix."""
        results = []
        for _ in range(count):
            try:
                tid = TypeID(prefix)
                results.append(str(tid))
            except Exception as e:
                raise ValueError(f"Error generating TypeID with prefix '{prefix}': {e}")
        return results

    def parse(self, typeid_str: str) -> Dict[str, Any]:
        """Parses a TypeID into its prefix and UUID components."""
        try:
            tid = TypeID.from_string(typeid_str)
            return {
                "valid": True,
                "typeid": str(tid),
                "prefix": tid.prefix,
                "uuid": str(tid.uuid)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

def run_typeid_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for TypeID Lab."""

    if args.action == "tui":
        try:
            from shared.tui import AgentTUI
            from pathlib import Path
            project_dir = getattr(args, "project_dir", Path("."))
            app = AgentTUI(project_dir=project_dir, start_tab="tab-typeid")

            import asyncio
            try:
                loop = asyncio.get_running_loop()
                asyncio.ensure_future(app.run_async())
            except RuntimeError:
                app.run()
                sys.exit(0)
            return True
        except ImportError as e:
            print(f"Error launching TUI: {e}", file=sys.stderr)
            return False

    try:
        manager = TypeIDLabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "generate":
        try:
            prefix = getattr(args, "prefix", "")
            count = getattr(args, "count", 1)

            results = manager.generate(prefix=prefix, count=count)
            for res in results:
                print(res)
            return True
        except Exception as e:
            print(f"Error generating TypeID: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "parse":
        typeid_str = getattr(args, "typeid", None)
        if not typeid_str:
            print("Error: typeid string is required for parse action.", file=sys.stderr)
            sys.exit(1)

        info = manager.parse(typeid_str)
        print(f"--- TypeID Inspection: {typeid_str} ---")
        if info["valid"]:
            print(f"Valid: Yes")
            print(f"Prefix: {info['prefix']}")
            print(f"UUID: {info['uuid']}")
            return True
        else:
            print(f"Valid: No")
            print(f"Error: {info.get('error')}")
            sys.exit(1)

    return False
