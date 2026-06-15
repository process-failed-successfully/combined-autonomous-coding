"""
Zip Lab
=======

Utilities for creating and extracting zip archives.
"""

import sys
import zipfile
from pathlib import Path
from typing import List, Optional


class ZipManager:
    """Manages zip archive creation and extraction."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def create(self, input_paths: List[Path], output_path: Path) -> Path:
        """Creates a zip archive from a list of paths."""
        if not input_paths:
            raise ValueError("No input paths provided")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for input_path in input_paths:
                if not input_path.exists():
                    print(f"Warning: Path not found: {input_path}", file=sys.stderr)
                    continue

                if input_path.is_file():
                    zf.write(input_path, input_path.name)
                elif input_path.is_dir():
                    for file_path in input_path.rglob("*"):
                        if file_path.is_file():
                            zf.write(file_path, file_path.relative_to(input_path.parent))
        return output_path

    def extract(self, input_path: Path, output_dir: Path) -> Path:
        """Extracts a zip archive to a directory."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file() or not input_path.name.endswith(".zip"):
            raise ValueError(f"Invalid archive format: {input_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(output_dir)
        return output_dir

    def list_contents(self, input_path: Path) -> List[str]:
        """Lists the contents of a zip archive."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file() or not input_path.name.endswith(".zip"):
            raise ValueError(f"Invalid archive format: {input_path}")

        contents = []
        with zipfile.ZipFile(input_path, "r") as zf:
            contents = zf.namelist()
        return contents


def run_zip_lab_logic(args):
    """Entry point for Zip Lab CLI."""
    if args.action == "tui":
        try:
            import asyncio
            from shared.tui_zip import ZipLabApp
            app = ZipLabApp()
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                asyncio.ensure_future(app.run_async())
            else:
                app.run()
        except ImportError:
            print("Error: Could not import ZipLabApp. Is Textual installed?", file=sys.stderr)
            sys.exit(1)
        return

    manager = ZipManager()

    try:
        if args.action == "create":
            if not args.inputs:
                print("Error: Input paths are required to create a zip.", file=sys.stderr)
                sys.exit(1)
            output = Path(args.output) if args.output else Path("archive.zip")
            inputs = [Path(p) for p in args.inputs]
            final_path = manager.create(inputs, output)
            print(f"Archive created at {final_path}")

        elif args.action == "extract":
            if not args.input:
                print("Error: Input archive is required to extract.", file=sys.stderr)
                sys.exit(1)
            output_dir = Path(args.output) if args.output else Path(".")
            input_path = Path(args.input)
            final_path = manager.extract(input_path, output_dir)
            print(f"Archive extracted to {final_path}")

        elif args.action == "list":
            if not getattr(args, "input", None):
                print("Error: Input archive is required to list contents.", file=sys.stderr)
                sys.exit(1)
            input_path = Path(args.input)
            contents = manager.list_contents(input_path)
            for item in contents:
                print(item)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
