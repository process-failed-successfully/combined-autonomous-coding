"""
Tar Lab
=======

Utilities for creating, listing, and extracting tar archives.
"""

import sys
import tarfile
from pathlib import Path
from typing import List, Optional, Any


class TarManager:
    """Manages tar archive creation, listing, and extraction."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def create(self, input_paths: List[Path], output_path: Path, compression: str = "gz") -> Path:
        """Creates a tar archive from a list of paths."""
        if not input_paths:
            raise ValueError("No input paths provided")

        mode = "w"
        if compression in ["gz", "bz2", "xz"]:
            mode = f"w:{compression}"
        elif compression == "":
            mode = "w"
        else:
            raise ValueError(f"Unsupported compression type: {compression}")

        with tarfile.open(output_path, mode) as tar:
            for input_path in input_paths:
                if not input_path.exists():
                    print(f"Warning: Path not found: {input_path}", file=sys.stderr)
                    continue
                # Add file or directory to tar. arcname determines the name inside the tar
                tar.add(input_path, arcname=input_path.name)
        return output_path

    def extract(self, input_path: Path, output_dir: Path) -> Path:
        """Extracts a tar archive to a directory."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"Not a file: {input_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(input_path, "r:*") as tar:
            tar.extractall(path=output_dir) # nosec B202
        return output_dir

    def list(self, input_path: Path) -> List[str]:
        """Lists the contents of a tar archive."""
        if not input_path.exists():
            raise FileNotFoundError(f"Archive not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"Not a file: {input_path}")

        with tarfile.open(input_path, "r:*") as tar:
            return tar.getnames()


def run_tar_lab_logic(args: Any):
    """Entry point for Tar Lab CLI."""
    manager = TarManager()

    try:
        if args.action == "create":
            if not getattr(args, 'inputs', None):
                print("Error: Input paths are required to create a tar archive.", file=sys.stderr)
                sys.exit(1)
            output = Path(args.output) if args.output else Path("archive.tar.gz")
            inputs = [Path(p) for p in args.inputs]
            compression = args.compression if hasattr(args, "compression") and args.compression else "gz"
            if compression == "none":
                compression = ""
            final_path = manager.create(inputs, output, compression)
            print(f"Archive created at {final_path}")

        elif args.action == "extract":
            if not getattr(args, 'input', None):
                print("Error: Input archive is required to extract.", file=sys.stderr)
                sys.exit(1)
            output_dir = Path(args.output) if args.output else Path(".")
            input_path = Path(args.input)
            final_path = manager.extract(input_path, output_dir)
            print(f"Archive extracted to {final_path}")

        elif args.action == "list":
            if not getattr(args, 'input', None):
                print("Error: Input archive is required to list.", file=sys.stderr)
                sys.exit(1)
            input_path = Path(args.input)
            names = manager.list(input_path)
            for name in names:
                print(name)

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
