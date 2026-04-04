import csv
import io
import sys
import yaml


class Csv2YamlManager:
    """Manager for converting CSV to YAML."""

    def convert_csv_to_yaml(self, csv_data: str, delimiter: str = ',') -> str:
        """Converts a CSV string to a YAML string."""
        if not csv_data.strip():
            return ""

        try:
            reader = csv.DictReader(io.StringIO(csv_data), delimiter=delimiter)
            rows = list(reader)

            # YAML doesn't have an "items" root required like our TOML impl,
            # but usually outputting a list of dicts is standard for CSV to YAML.
            return yaml.dump(rows, sort_keys=False, default_flow_style=False)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV or generate YAML: {e}")


def run_csv2yaml_lab_logic(args) -> bool:
    """Runs the CSV to YAML Lab logic for CLI."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Csv2Yaml Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-csv2yaml")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        return True

    manager = Csv2YamlManager()

    csv_data = None
    if getattr(args, "text", None):
        csv_data = args.text
    elif getattr(args, "file", None):
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                csv_data = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif not sys.stdin.isatty():
        csv_data = sys.stdin.read()

    if not csv_data:
        print("Error: No input provided. Use --text, --file, or pipe input.", file=sys.stderr)
        return False

    delimiter = getattr(args, "delimiter", ",")

    try:
        yaml_output = manager.convert_csv_to_yaml(csv_data, delimiter=delimiter)

        if getattr(args, "output", None):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(yaml_output)
            print(f"Output written to {args.output}")
        else:
            print(yaml_output)
        return True
    except Exception as e:
        print(f"Error converting CSV to YAML: {e}", file=sys.stderr)
        return False
