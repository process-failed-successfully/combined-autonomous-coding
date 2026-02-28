import sys
from pathlib import Path

class SetLabManager:
    def process_sets(self, set1_lines, set2_lines, operation, ignore_case=False, trim_whitespace=False):
        if trim_whitespace:
            set1_lines = [line.strip() for line in set1_lines]
            set2_lines = [line.strip() for line in set2_lines]

        if ignore_case:
            set1 = {line.lower() for line in set1_lines}
            set2 = {line.lower() for line in set2_lines}
            # Need original mapping for output
            set1_orig = {line.lower(): line for line in set1_lines}
            set2_orig = {line.lower(): line for line in set2_lines}
        else:
            set1 = set(set1_lines)
            set2 = set(set2_lines)

        if operation == "union":
            result = set1.union(set2)
        elif operation == "intersection":
            result = set1.intersection(set2)
        elif operation == "difference":
            result = set1.difference(set2)
        elif operation == "symmetric_difference":
            result = set1.symmetric_difference(set2)
        elif operation == "subset":
            return {"success": True, "result": [str(set1.issubset(set2))], "is_boolean": True}
        elif operation == "superset":
            return {"success": True, "result": [str(set1.issuperset(set2))], "is_boolean": True}
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        if ignore_case:
            # Map back to original case where possible. Prefer set1's case if present, else set2
            final_result = []
            for item in result:
                if item in set1_orig:
                    final_result.append(set1_orig[item])
                elif item in set2_orig:
                    final_result.append(set2_orig[item])
                else:
                    final_result.append(item)
            return {"success": True, "result": sorted(final_result), "is_boolean": False}
        else:
            return {"success": True, "result": sorted(list(result)), "is_boolean": False}

def run_set_lab_logic(args):
    manager = SetLabManager()

    def get_lines(input_str, file_path):
        if getattr(args, input_str, None):
            return getattr(args, input_str).split(',')
        elif getattr(args, file_path, None):
            path = Path(getattr(args, file_path))
            if not path.exists():
                print(f"Error: File not found: {getattr(args, file_path)}", file=sys.stderr)
                sys.exit(1)
            return path.read_text().splitlines()
        return []

    set1_lines = get_lines('set1', 'file1')
    set2_lines = get_lines('set2', 'file2')

    if not set1_lines and not set2_lines:
        print("Error: Must provide sets either via --set1/--set2 or --file1/--file2", file=sys.stderr)
        sys.exit(1)

    result = manager.process_sets(set1_lines, set2_lines, args.operation, getattr(args, 'ignore_case', False), getattr(args, 'trim_whitespace', False))

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if result.get("is_boolean"):
        print(result["result"][0])
    else:
        for item in result["result"]:
            print(item)
