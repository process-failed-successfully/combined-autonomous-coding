import configparser
import json
import sys
from pathlib import Path
from typing import Any, Dict, Union


class Ini2JsonManager:
    """Manages the conversion of INI data to JSON format."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def convert(self, ini_data: str) -> str:
        """Converts INI string data to a JSON string."""
        config = configparser.ConfigParser()
        # To prevent configparser from converting keys to lowercase:
        config.optionxform = str

        try:
            config.read_string(ini_data)
        except configparser.Error as e:
            raise ValueError(f"Invalid INI string: {e}")

        result: Dict[str, Any] = {}

        # Default section
        if config.defaults():
            result["DEFAULT"] = dict(config.defaults())

        for section in config.sections():
            result[section] = {}
            for key in config.options(section):
                val = config.get(section, key)
                val_lower = val.lower()
                if val_lower == "true":
                    result[section][key] = True
                elif val_lower == "false":
                    result[section][key] = False
                else:
                    try:
                        # Try parsing as float first to handle decimals
                        float_val = float(val)
                        # If it's an integer (like 42.0 or -42), convert it to int
                        if float_val.is_integer():
                            result[section][key] = int(float_val)
                        else:
                            result[section][key] = float_val
                    except ValueError:
                        result[section][key] = val

        return json.dumps(result, indent=2)


def run_ini2json_lab_logic(args):
    """CLI handler for INI to JSON conversion."""
    manager = Ini2JsonManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching INI to JSON Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-ini2json")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
            return
        else:
            app.run()
        sys.exit(0)

    # CLI mode
    try:
        input_data = None
        if hasattr(args, "file") and args.file:
            input_path = Path(args.file)
            if not input_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            input_data = input_path.read_text(encoding="utf-8")
        elif hasattr(args, "text") and args.text:
            input_data = args.text
        elif not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()

        if not input_data:
            print("Error: No input provided. Provide --file, --text, or pass INI via stdin.", file=sys.stderr)
            sys.exit(1)

        json_output = manager.convert(input_data)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(json_output, encoding="utf-8")
            print(f"✅ Converted JSON saved to {args.output}")
        else:
            print(json_output, end="")

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
