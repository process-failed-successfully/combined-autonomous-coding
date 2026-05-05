import configparser
import json
import sys
from pathlib import Path
from typing import Any, Dict, Union


class Ini2JsonManager:
    """Manages the conversion of INI format data to JSON."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def convert(self, ini_data: str) -> str:
        """Converts INI string data to JSON string."""
        config = configparser.ConfigParser()
        # Preserve original case for keys
        config.optionxform = str

        try:
            config.read_string(ini_data)
        except configparser.MissingSectionHeaderError:
            # If there's no section header, we need to extract lines that are key-values
            # and prefix them, without duplicating existing sections if they follow.
            try:
                # Use a dummy section for the start
                config.read_string(f"[DEFAULT]\n{ini_data}")
            except configparser.Error as e:
                raise ValueError(f"Invalid INI string: {e}")
        except configparser.Error as e:
            raise ValueError(f"Invalid INI string: {e}")

        data: Dict[str, Any] = {}

        # Add default section items if any
        defaults = config.defaults()
        if defaults:
            # Check if there are other sections to decide if we nest it or not
            if config.sections():
                data["DEFAULT"] = dict(defaults)
            else:
                data.update(defaults)

        for sec in config.sections():
            # If the only section was added automatically by our json2ini, it might be 'Global'
            if sec == "Global" and len(config.sections()) == 1 and not defaults:
                data.update(dict(config.items(sec)))
            else:
                data[sec] = dict(config.items(sec))

        return json.dumps(data, indent=2)


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
            return

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
