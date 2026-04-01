import csv
import io
import sys
import tomlkit


class Csv2TomlManager:
    """Manager for converting CSV to TOML."""

    def convert_csv_to_toml(self, csv_data: str, delimiter: str = ',') -> str:
        """Converts a CSV string to a TOML string."""
        if not csv_data.strip():
            return ""

        try:
            reader = csv.DictReader(io.StringIO(csv_data), delimiter=delimiter)

            # Use tomlkit to build the TOML document
            doc = tomlkit.document()
            items = tomlkit.aot()

            for row in reader:
                # Convert DictReader row to a standard dict and add to array of tables
                table = tomlkit.table()
                for key, value in row.items():
                    # Handle None keys (can happen with jagged CSVs)
                    k = str(key) if key is not None else "unknown"
                    v = str(value) if value is not None else ""
                    table.add(k, v)
                items.append(table)

            if items:
                doc.add("items", items)

            return tomlkit.dumps(doc)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV or generate TOML: {e}")


def run_csv2toml_lab_logic(args) -> bool:
    """Runs the CSV to TOML Lab logic for CLI."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Csv2Toml Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-csv2toml")
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

    manager = Csv2TomlManager()

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
        toml_output = manager.convert_csv_to_toml(csv_data, delimiter=delimiter)

        if getattr(args, "output", None):
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(toml_output)
            print(f"Output written to {args.output}")
        else:
            print(toml_output)
        return True
    except Exception as e:
        print(f"Error converting CSV to TOML: {e}", file=sys.stderr)
        return False
