"""
Set Lab
=======

Utilities for set operations on lists/files.
"""

import sys
from pathlib import Path
from typing import List, Set, Union, Optional

class SetLabManager:
    """Manages set operations on collections of strings."""

    def _prepare_data(self, data: List[str], ignore_case: bool = False, trim: bool = False) -> List[str]:
        result = data
        if trim:
            result = [item.strip() for item in result]
        if ignore_case:
            result = [item.lower() for item in result]
        # Filter out empty lines if trim was applied, or let user keep them?
        # Usually sets of empty strings are not very useful, but we'll leave them to be mathematically correct,
        # unless we want to filter them explicitly. We'll leave them.
        return result

    def _to_original_case_map(self, original_data: List[str], prepared_data: List[str]) -> dict:
        """Helper to map prepared keys back to the first original value encountered."""
        mapping = {}
        for orig, prep in zip(original_data, prepared_data):
            if prep not in mapping:
                mapping[prep] = orig
        return mapping

    def perform_operation(self, list_a: List[str], list_b: List[str], operation: str, ignore_case: bool = False, trim: bool = False) -> Union[List[str], bool]:
        prep_a = self._prepare_data(list_a, ignore_case, trim)
        prep_b = self._prepare_data(list_b, ignore_case, trim)

        set_a = set(prep_a)
        set_b = set(prep_b)

        # Build mapping for restoring original case if ignore_case was used
        # We restore the case from A if it exists in A, else B.
        orig_map = {}
        if ignore_case:
            map_b = self._to_original_case_map(list_b, prep_b)
            map_a = self._to_original_case_map(list_a, prep_a)
            # A takes precedence
            orig_map.update(map_b)
            orig_map.update(map_a)
        elif trim:
            # Still need to restore untrimmed? No, usually if user asks to trim, they want trimmed output.
            pass

        def _restore(result_set: Set[str]) -> List[str]:
            sorted_res = sorted(list(result_set))
            if ignore_case:
                return [orig_map[item] for item in sorted_res]
            return sorted_res

        if operation == "union":
            return _restore(set_a.union(set_b))
        elif operation == "intersect":
            return _restore(set_a.intersection(set_b))
        elif operation == "difference":
            return _restore(set_a.difference(set_b))
        elif operation == "sym_diff":
            return _restore(set_a.symmetric_difference(set_b))
        elif operation == "is_subset":
            return set_a.issubset(set_b)
        elif operation == "is_superset":
            return set_a.issuperset(set_b)
        else:
            raise ValueError(f"Unknown operation: {operation}")

def run_set_lab_logic(args) -> bool:
    """CLI logic for Set Lab."""

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Set Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-set")
        app.run()
        return True

    manager = SetLabManager()

    def load_list(input_str: str) -> List[str]:
        if not input_str:
            return []
        path = Path(input_str)
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8").splitlines()
        # If not a file, treat as comma-separated
        return [s for s in input_str.split(",") if s]

    list_a = load_list(args.list_a)
    list_b = load_list(args.list_b)

    if not list_a and not list_b:
        print("Error: Both lists are empty.", file=sys.stderr)
        return False

    try:
        result = manager.perform_operation(
            list_a, list_b,
            operation=args.action,
            ignore_case=args.ignore_case,
            trim=args.trim
        )

        if isinstance(result, bool):
            print(str(result))
        else:
            for item in result:
                print(item)

        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
