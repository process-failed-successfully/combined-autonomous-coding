"""
INI Lab
=======

Utilities for managing and converting INI configuration files.
"""

import sys
import json
from pathlib import Path
import configparser
from typing import List, Dict, Any

from rich.console import Console

console = Console()


class IniLabManager:
    """Manages INI file operations."""

    def __init__(self):
        pass

    def _read_config(self, filepath: Path) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        # Preserve original case for keys
        config.optionxform = str
        if filepath.exists():
            config.read(filepath, encoding="utf-8")
        return config

    def _write_config(self, config: configparser.ConfigParser, filepath: Path):
        with open(filepath, "w", encoding="utf-8") as f:
            config.write(f)

    def get(self, filepath: str, section: str, key: str) -> str:
        """Gets a value from the INI file."""
        config = self._read_config(Path(filepath))
        if config.has_section(section) and config.has_option(section, key):
            return config.get(section, key)
        return ""

    def set(self, filepath: str, section: str, key: str, value: str):
        """Sets a value in the INI file."""
        path = Path(filepath)
        config = self._read_config(path)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
        self._write_config(config, path)

    def delete(self, filepath: str, section: str, key: str = None):
        """Deletes a key or an entire section from the INI file."""
        path = Path(filepath)
        config = self._read_config(path)
        if not config.has_section(section):
            return

        if key:
            config.remove_option(section, key)
        else:
            config.remove_section(section)
        self._write_config(config, path)

    def sections(self, filepath: str) -> List[str]:
        """Lists all sections in the INI file."""
        config = self._read_config(Path(filepath))
        return config.sections()

    def keys(self, filepath: str, section: str) -> List[str]:
        """Lists all keys in a given section."""
        config = self._read_config(Path(filepath))
        if config.has_section(section):
            return config.options(section)
        return []

    def to_json(self, filepath: str) -> str:
        """Converts an INI file to a JSON string."""
        config = self._read_config(Path(filepath))
        data: Dict[str, Any] = {}
        for sec in config.sections():
            data[sec] = {}
            for k, v in config.items(sec):
                data[sec][k] = v
        return json.dumps(data, indent=2)

    def from_json(self, json_data: str, filepath: str):
        """Converts JSON data to an INI file."""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("JSON data must be a dictionary to convert to INI.")

        config = configparser.ConfigParser()
        config.optionxform = str

        for sec, items in data.items():
            if not isinstance(items, dict):
                # INI format requires sections to have key-value pairs
                continue
            config.add_section(str(sec))
            for k, v in items.items():
                config.set(str(sec), str(k), str(v))

        self._write_config(config, Path(filepath))


def run_ini_lab_logic(args) -> bool:
    """CLI logic for the INI lab."""
    manager = IniLabManager()

    try:
        if args.action == "get":
            val = manager.get(args.file, args.section, args.key)
            if val:
                print(val)

        elif args.action == "set":
            manager.set(args.file, args.section, args.key, args.value)
            console.print(f"[green]Set {args.section}.{args.key} = {args.value} in {args.file}[/green]")

        elif args.action == "del":
            manager.delete(args.file, args.section, args.key)
            if args.key:
                console.print(f"[green]Deleted {args.section}.{args.key} from {args.file}[/green]")
            else:
                console.print(f"[green]Deleted section {args.section} from {args.file}[/green]")

        elif args.action == "sections":
            secs = manager.sections(args.file)
            for s in secs:
                print(s)

        elif args.action == "keys":
            keys = manager.keys(args.file, args.section)
            for k in keys:
                print(k)

        elif args.action == "to-json":
            js = manager.to_json(args.file)
            print(js)

        elif args.action == "from-json":
            if not sys.stdin.isatty():
                data = sys.stdin.read()
            else:
                if not args.json_input:
                    console.print("[red]Error: JSON input string or piped stdin required.[/red]")
                    return False
                data = args.json_input
            manager.from_json(data, args.file)
            console.print(f"[green]Wrote JSON to {args.file}[/green]")

        return True
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False
