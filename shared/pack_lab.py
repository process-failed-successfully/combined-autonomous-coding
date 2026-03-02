import sys
import subprocess
import fnmatch
from pathlib import Path
from typing import List, Optional

class PackManager:
    """Manages packing a codebase into a single text format (Markdown or XML)."""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir).resolve()

    def get_files(self, include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """Gets all tracked and non-ignored files using git ls-files."""
        try:
            # Get tracked files
            tracked_cmd = ["git", "-C", str(self.project_dir), "ls-files"]
            tracked_result = subprocess.run(tracked_cmd, capture_output=True, text=True, check=True)
            files = tracked_result.stdout.splitlines()

            # Get untracked but non-ignored files
            untracked_cmd = ["git", "-C", str(self.project_dir), "ls-files", "--others", "--exclude-standard"]
            untracked_result = subprocess.run(untracked_cmd, capture_output=True, text=True, check=True)
            files.extend(untracked_result.stdout.splitlines())

        except subprocess.CalledProcessError as e:
            # Fallback if not a git repo or git fails
            print(f"Warning: git ls-files failed: {e}. Falling back to rglob.", file=sys.stderr)
            files = [str(p.relative_to(self.project_dir)) for p in self.project_dir.rglob("*") if p.is_file()]

        # Filter out empty strings
        files = [f for f in files if f.strip()]

        # Apply include patterns
        if include_patterns:
            included_files = set()
            for pattern in include_patterns:
                included_files.update(fnmatch.filter(files, pattern))
            files = list(included_files)

        # Apply exclude patterns
        if exclude_patterns:
            excluded_files = set()
            for pattern in exclude_patterns:
                excluded_files.update(fnmatch.filter(files, pattern))
            files = [f for f in files if f not in excluded_files]

        # Convert to Path objects
        # Ignore binary files by checking extension or read try
        final_files = []
        for f in sorted(files):
            path = self.project_dir / f
            if path.is_file() and not self._is_binary(path):
                final_files.append(path)

        return final_files

    def _is_binary(self, path: Path) -> bool:
        """Heuristically checks if a file is binary."""
        # Check by extension first for speed
        binary_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".tiff", ".bmp",
            ".pdf", ".exe", ".dll", ".so", ".dylib", ".zip", ".tar", ".gz",
            ".tgz", ".bz2", ".7z", ".pyc", ".pyo", ".pyd", ".db", ".sqlite",
            ".sqlite3", ".mp4", ".mp3", ".wav", ".avi", ".mov", ".mkv", ".flv",
            ".woff", ".woff2", ".ttf", ".eot", ".bin", ".dat", ".pkl", ".pkl.gz"
        }
        if path.suffix.lower() in binary_extensions:
            return True

        # Check by reading first block
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                if b"\0" in chunk:
                    return True
        except IOError:
            # If we can't read it, skip it
            return True
        return False

    def pack(self, files: List[Path], format: str = "markdown") -> str:
        """Packs the contents of the files into a single string."""
        if format == "xml":
            return self._pack_xml(files)
        else:
            return self._pack_markdown(files)

    def _pack_markdown(self, files: List[Path]) -> str:
        output = []
        for file in files:
            try:
                rel_path = file.relative_to(self.project_dir)
                content = file.read_text(encoding='utf-8', errors='replace')
                ext = file.suffix.lstrip('.')
                output.append(f"### File: {rel_path}")
                output.append(f"```{ext}")
                output.append(content)
                output.append("```\n")
            except Exception as e:
                output.append(f"### File: {file.relative_to(self.project_dir)}")
                output.append(f"Error reading file: {e}\n")
        return "\n".join(output)

    def _pack_xml(self, files: List[Path]) -> str:
        output = ["<repository>"]
        for file in files:
            try:
                rel_path = file.relative_to(self.project_dir)
                content = file.read_text(encoding='utf-8', errors='replace')

                output.append(f'  <file path="{rel_path}">')
                output.append(f'<![CDATA[\n{content}\n]]>')
                output.append('  </file>')
            except Exception as e:
                output.append(f'  <file path="{file.relative_to(self.project_dir)}">')
                output.append(f'    <error>{e}</error>')
                output.append('  </file>')
        output.append("</repository>")
        return "\n".join(output)

def run_pack_logic(args) -> bool:
    """CLI Entry point for Pack Lab."""
    manager = PackManager(args.project_dir)

    include_patterns = args.include.split(",") if args.include else None
    exclude_patterns = args.exclude.split(",") if args.exclude else None

    # Automatically exclude some common noisy directories if not explicitly included
    default_excludes = ["*.git*", "node_modules/*", "venv/*", ".venv/*", "env/*", "__pycache__/*", "*.egg-info/*"]
    if not exclude_patterns:
        exclude_patterns = default_excludes
    else:
        exclude_patterns.extend(default_excludes)

    try:
        files = manager.get_files(include_patterns=include_patterns, exclude_patterns=exclude_patterns)

        if not files:
            print("No files found to pack.")
            return True

        packed_content = manager.pack(files, format=args.format)

        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = args.project_dir / output_path

            output_path.write_text(packed_content, encoding='utf-8')
            print(f"Successfully packed {len(files)} files into {output_path}")
        else:
            print(packed_content)

        return True
    except Exception as e:
        print(f"Error packing repository: {e}", file=sys.stderr)
        return False
