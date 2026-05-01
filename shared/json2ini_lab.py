import configparser
import json
import sys
import io
from pathlib import Path
from typing import Any, Dict, Union


class Json2IniManager:
    """Manages the conversion of JSON data to INI format."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def _process_value(self, value: Any) -> str:
        """Converts various Python types to strings suitable for INI."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return ""
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def convert(self, json_data: Union[str, Dict[str, Any]]) -> str:
        """Converts JSON data to INI string."""
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        else:
            data = json_data

        if not isinstance(data, dict):
            raise ValueError("JSON data must be a dictionary to be converted to INI.")

        config = configparser.ConfigParser()
        # To prevent configparser from converting keys to lowercase:
        config.optionxform = str

        # Default section for top-level primitives
        top_level_primitives = {}

        for key, value in data.items():
            if isinstance(value, dict):
                # Nested dicts become sections
                config.add_section(key)
                for sub_key, sub_value in value.items():
                    config.set(key, str(sub_key), self._process_value(sub_value))
            else:
                top_level_primitives[key] = self._process_value(value)

        # Add global properties if present
        if top_level_primitives:
            # We must create a 'DEFAULT' section or a named section like 'Global'
            # Let's use a dummy section 'Global' since INI requires sections,
            # or we can use DEFAULT. configparser automatically writes DEFAULT without the [DEFAULT] header
            # depending on how it's saved. But let's add a "Global" section.
            config.add_section("Global")
            for k, v in top_level_primitives.items():
                config.set("Global", str(k), v)

        output = io.StringIO()
        config.write(output)

        # If we had a Global section and it's the only one, we can format it differently,
        # but configparser writes [Global].
        return output.getvalue()


def run_json2ini_lab_logic(args):
    """CLI handler for JSON to INI conversion."""
    manager = Json2IniManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to INI Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2ini")
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

        if not input_data:
            print("Error: No input provided. Provide --file, --text, or pass JSON via stdin.", file=sys.stderr)
            sys.exit(1)

        ini_output = manager.convert(input_data)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(ini_output, encoding="utf-8")
            print(f"✅ Converted INI saved to {args.output}")
        else:
            print(ini_output, end="")

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
