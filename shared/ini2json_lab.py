import configparser
import json
import sys
from pathlib import Path
from typing import Any, Dict


class Ini2JsonManager:
    """Manages the conversion of INI data to JSON format."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def convert(self, ini_data: str) -> str:
        """Converts INI string to JSON string."""
        if not ini_data or not ini_data.strip():
            return "{}"

        config = configparser.ConfigParser()
        # To prevent configparser from converting keys to lowercase
        config.optionxform = str

        try:
            config.read_string(ini_data)
        except configparser.Error as e:
            raise ValueError(f"Invalid INI string: {e}")

        result: Dict[str, Any] = {}

        for section in config.sections():
            result[section] = {}
            for key, val in config.items(section):
                # Optionally, attempt to parse ints/floats/bools
                # But typically INI values are left as strings
                # Let's do basic type conversion for cleaner JSON
                lower_val = val.lower()
                if lower_val in ('true', 'yes', 'on'):
                    parsed_val = True
                elif lower_val in ('false', 'no', 'off'):
                    parsed_val = False
                elif val.isdigit():
                    parsed_val = int(val)
                else:
                    try:
                        parsed_val = float(val)
                    except ValueError:
                        parsed_val = val

                result[section][key] = parsed_val

        # Also grab anything in the DEFAULT section if used
        if config.defaults():
            if 'DEFAULT' not in result:
                result['DEFAULT'] = {}
            for key, val in config.defaults().items():
                lower_val = val.lower()
                if lower_val in ('true', 'yes', 'on'):
                    parsed_val = True
                elif lower_val in ('false', 'no', 'off'):
                    parsed_val = False
                elif val.isdigit():
                    parsed_val = int(val)
                else:
                    try:
                        parsed_val = float(val)
                    except ValueError:
                        parsed_val = val
                result['DEFAULT'][key] = parsed_val

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

        if input_data is None:
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
