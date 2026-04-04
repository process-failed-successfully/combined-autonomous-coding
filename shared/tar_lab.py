"""
Tar Lab
=======

Utilities for creating, extracting, and listing tar archives.
"""

import sys
import tarfile
from pathlib import Path
from typing import List, Optional


class TarManager:
    """Manages tar archive creation, extraction, and listing."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def create(self, input_paths: List[Path], output_path: Path, compression: str = "") -> Path:
        """Creates a tar archive from a list of paths."""
        if not input_paths:
            raise ValueError("No input paths provided")

        mode = "w"
        if compression:
            mode = f"w:{compression}"

        with tarfile.open(output_path, mode) as tf:
            for input_path in input_paths:
                if not input_path.exists():
                    print(f"Warning: Path not found: {input_path}", file=sys.stderr)
                    continue
                tf.add(input_path, arcname=input_path.name)
        return output_path

    def extract(self, input_path: Path, output_dir: Path) -> Path:
        """Extracts a tar archive to a directory."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"Invalid file: {input_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(input_path, "r:*") as tf:
            if hasattr(tarfile, 'data_filter'):
                tf.extractall(output_dir, filter='data')
            else:
                tf.extractall(output_dir) # nosec B202
        return output_dir

    def list_contents(self, input_path: Path) -> List[str]:
        """Lists the contents of a tar archive."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"Invalid file: {input_path}")

        contents = []
        with tarfile.open(input_path, "r:*") as tf:
            for member in tf.getmembers():
                contents.append(member.name)
        return contents


async def run_tar_lab_logic(args):
    """Entry point for Tar Lab CLI."""
    if args.action == "tui":
        try:
            import asyncio
            from shared.tui_tar import TarLabApp
            app = TarLabApp(project_dir=getattr(args, 'project_dir', None))
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                await app.run_async()
            else:
                app.run()
        except ImportError as e:
            print(f"Error: Could not import TarLabApp. Is Textual installed? {e}", file=sys.stderr)
            sys.exit(1)
        return

    manager = TarManager()

    try:
        if args.action == "create":
            if not args.inputs:
                print("Error: Input paths are required to create a tar archive.", file=sys.stderr)
                sys.exit(1)
            output = Path(args.output) if args.output else Path("archive.tar")
            inputs = [Path(p) for p in args.inputs]
            compression = args.compression if hasattr(args, 'compression') and args.compression else ""
            final_path = manager.create(inputs, output, compression=compression)
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
            if not args.input:
                print("Error: Input archive is required to list contents.", file=sys.stderr)
                sys.exit(1)
            input_path = Path(args.input)
            contents = manager.list_contents(input_path)
            for item in contents:
                print(item)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
