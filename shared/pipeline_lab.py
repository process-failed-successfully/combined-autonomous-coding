"""
Pipeline Lab (pipe-lab)
=======================

A CLI tool for chaining text and data transformations.
Allows piping data through a sequence of operations like `jq` or `CyberChef` but for the command line.

Usage:
  pipe "input" --do "upper" --do "base64-encode"
  cat file.json | pipe --do "json-parse" --do "json-get user.name"
"""

import sys
import json
import base64
import binascii
import urllib.parse
import re
from typing import Any, List, Union, Callable
from pathlib import Path

class PipelineLabManager:
    """Manages the pipeline execution context and operations."""

    def __init__(self):
        self.operations = self._register_operations()

    def _register_operations(self) -> dict:
        """Registers available operations."""
        return {
            # Text
            "upper": str.upper,
            "lower": str.lower,
            "title": str.title,
            "capitalize": str.capitalize,
            "reverse": lambda x: x[::-1],
            "strip": str.strip,
            "lstrip": str.lstrip,
            "rstrip": str.rstrip,

            # Encoding
            "base64-encode": self._base64_encode,
            "base64-decode": self._base64_decode,
            "hex-encode": self._hex_encode,
            "hex-decode": self._hex_decode,
            "url-encode": self._url_encode,
            "url-decode": self._url_decode,

            # JSON
            "json-parse": self._json_parse,
            "json-stringify": self._json_stringify,
            "json-get": self._json_get,
            "json-keys": self._json_keys,
            "json-values": self._json_values,

            # List/Lines
            "split": self._split,
            "join": self._join,
            "lines": lambda x: x.splitlines(),
            "sort": sorted,
            "unique": lambda x: list(set(x)), # Note: set creates unique but unordered
            "count": len,
            "first": self._first,
            "last": self._last,
            "slice": self._slice,
            "map": self._map,

            # Filter
            "grep": self._grep,
            "exclude": self._exclude,

            # Math (for lists of numbers)
            "sum": sum,
            "min": min,
            "max": max,
            "avg": self._avg,

            # Debug
            "debug": self._debug,
            "type": self._type,
        }

    def process(self, data: Any, operations: List[str]) -> Any:
        """Processes the input data through a sequence of operations."""
        current_value = data

        for op_str in operations:
            parts = op_str.split(" ", 1)
            op_name = parts[0]
            op_arg = parts[1] if len(parts) > 1 else None

            if op_name not in self.operations:
                raise ValueError(f"Unknown operation: {op_name}")

            func = self.operations[op_name]

            try:
                if op_arg is not None:
                    current_value = func(current_value, op_arg)
                else:
                    # Check if function accepts an argument (some might be optional)
                    # For simplicity, we assume if no arg provided, calling without arg
                    current_value = func(current_value)
            except Exception as e:
                raise ValueError(f"Error in operation '{op_name}': {e}")

        return current_value

    # --- Operation Implementations ---

    def _base64_encode(self, data: Any) -> str:
        if not isinstance(data, (str, bytes)):
            data = str(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')

    def _base64_decode(self, data: str) -> str:
        if not isinstance(data, str):
             raise ValueError("base64-decode input must be string")
        # Add padding if needed
        padding = len(data) % 4
        if padding:
            data += '=' * (4 - padding)
        return base64.b64decode(data).decode('utf-8')

    def _hex_encode(self, data: Any) -> str:
        if isinstance(data, str):
            data = data.encode('utf-8')
        return binascii.hexlify(data).decode('utf-8')

    def _hex_decode(self, data: str) -> str:
        if isinstance(data, str):
             # Remove spaces
             data = data.replace(" ", "")
        return binascii.unhexlify(data).decode('utf-8')

    def _url_encode(self, data: str) -> str:
        return urllib.parse.quote(str(data))

    def _url_decode(self, data: str) -> str:
        return urllib.parse.unquote(str(data))

    def _json_parse(self, data: str) -> Any:
        return json.loads(data)

    def _json_stringify(self, data: Any) -> str:
        return json.dumps(data, indent=2)

    def _json_get(self, data: Any, path: str) -> Any:
        """Simple dot notation get."""
        keys = path.replace('[', '.').replace(']', '').split('.')
        current = data
        for key in keys:
            if not key: continue
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    idx = int(key)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
            if current is None:
                return None
        return current

    def _json_keys(self, data: dict) -> List[str]:
        if not isinstance(data, dict):
            raise ValueError("Input must be a dict")
        return list(data.keys())

    def _json_values(self, data: dict) -> List[Any]:
         if not isinstance(data, dict):
            raise ValueError("Input must be a dict")
         return list(data.values())

    def _split(self, data: str, delim: str = " ") -> List[str]:
        return data.split(delim)

    def _join(self, data: List[str], delim: str = "") -> str:
        return delim.join(map(str, data))

    def _first(self, data: List[Any], n: str = "1") -> Any:
        count = int(n)
        if count == 1:
            return data[0] if data else None
        return data[:count]

    def _last(self, data: List[Any], n: str = "1") -> Any:
        count = int(n)
        if count == 1:
            return data[-1] if data else None
        return data[-count:]

    def _slice(self, data: List[Any], arg: str) -> List[Any]:
        # format: start:end or start:end:step
        parts = [int(p) if p else None for p in arg.split(':')]
        return data[slice(*parts)]

    def _map(self, data: List[Any], op: str) -> List[Any]:
        """Applies a single operation to each item in the list."""
        # This is a mini-pipeline for each item
        return [self.process(item, [op]) for item in data]

    def _grep(self, data: List[str], pattern: str) -> List[str]:
        regex = re.compile(pattern)
        return [item for item in data if regex.search(str(item))]

    def _exclude(self, data: List[str], pattern: str) -> List[str]:
        regex = re.compile(pattern)
        return [item for item in data if not regex.search(str(item))]

    def _avg(self, data: List[Union[int, float]]) -> float:
        if not data: return 0
        return sum(data) / len(data)

    def _debug(self, data: Any) -> Any:
        print(f"DEBUG: {data!r} (Type: {type(data).__name__})", file=sys.stderr)
        return data

    def _type(self, data: Any) -> str:
        return type(data).__name__


def run_pipeline_lab_logic(args):
    """CLI entry point for Pipeline Lab."""
    manager = PipelineLabManager()

    # 1. Get Input
    content = None
    if args.input:
        if args.input == "-":
            content = sys.stdin.read()
        else:
            path = Path(args.input)
            if path.exists():
                # Try reading as text
                try:
                    content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    # Fallback to binary? No, pipeline is mostly text-based for now.
                    # Or maybe read as binary if first op handles bytes?
                    # For simplicity, stick to text.
                     print(f"Error: Could not read file {path} as UTF-8 text.", file=sys.stderr)
                     sys.exit(1)
            else:
                # Treat argument as direct input string
                content = args.input
    elif not sys.stdin.isatty():
        # Pipe input
        content = sys.stdin.read()

    if content is None:
        print("Error: No input provided. Use stdin or argument.", file=sys.stderr)
        sys.exit(1)

    # 2. Get Operations
    ops = args.do
    if not ops:
        print("Error: No operations specified. Use --do <op>.", file=sys.stderr)
        print("Available operations:", ", ".join(sorted(manager.operations.keys())), file=sys.stderr)
        sys.exit(1)

    # 3. Process
    try:
        result = manager.process(content, ops)

        # 4. Output
        if isinstance(result, (dict, list)):
            # Auto-stringify if final result is obj
            print(json.dumps(result, indent=2))
        else:
            print(result)

    except Exception as e:
        print(f"Pipeline Error: {e}", file=sys.stderr)
        sys.exit(1)
