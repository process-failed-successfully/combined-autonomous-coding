import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

class JsonlManager:
    """Manages conversion and validation between JSON and JSON Lines formats."""

    def json_to_jsonl(self, json_data: str) -> str:
        """Converts a JSON array of objects to JSON Lines."""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")

        if not isinstance(data, list):
            raise ValueError("Input JSON must be an array of objects to convert to JSON Lines.")

        jsonl_lines = []
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("All items in the input JSON array must be objects (dictionaries).")
            # Convert each object back to a compact JSON string and append to the lines
            jsonl_lines.append(json.dumps(item, separators=(',', ':')))

        return "\n".join(jsonl_lines)

    def jsonl_to_json(self, jsonl_data: str, indent: int = 2) -> str:
        """Converts JSON Lines to a JSON array of objects."""
        lines = jsonl_data.strip().split('\n')
        json_array = []

        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                     raise ValueError(f"Line {i} is not a JSON object.")
                json_array.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {i}: {e}")

        return json.dumps(json_array, indent=indent)

    def validate_jsonl(self, jsonl_data: str) -> Tuple[bool, str]:
        """Validates if the string is valid JSON Lines."""
        lines = jsonl_data.strip().split('\n')
        if not jsonl_data.strip():
            return False, "Input data is empty."

        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    return False, f"Line {i} is valid JSON but not a JSON object."
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON at line {i}: {e}"

        return True, "Valid JSON Lines."


def run_jsonl_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Jsonl Lab."""
    manager = JsonlManager()

    action = getattr(args, "action", None)
    if action not in ("json2jsonl", "jsonl2json", "validate"):
        print(f"Error: Invalid action '{action}'.", file=sys.stderr)
        return False

    input_data = getattr(args, "input", None)
    if not input_data:
        if not sys.stdin.isatty():
            input_data = sys.stdin.read()
        else:
            print("Error: Input required.", file=sys.stderr)
            return False

    # Check if input is a file
    try:
        if len(input_data) < 1000 and Path(input_data).exists() and Path(input_data).is_file():
            content = Path(input_data).read_text(encoding="utf-8")
        else:
            content = input_data
    except Exception:
        content = input_data

    try:
        result = ""
        if action == "json2jsonl":
            result = manager.json_to_jsonl(content)
        elif action == "jsonl2json":
            result = manager.jsonl_to_json(content)
        elif action == "validate":
            is_valid, msg = manager.validate_jsonl(content)
            print(msg)
            return is_valid

        output = getattr(args, "output", None)
        if output:
            Path(output).write_text(result, encoding="utf-8")
            print(f"Output written to {output}")
        else:
            print(result)

        return True
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
