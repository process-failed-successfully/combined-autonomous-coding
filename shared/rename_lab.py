import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from shared.text_lab import TextLabManager

try:
    from rich.console import Console
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None


class RenameLabManager:
    """Manages file renaming operations: regex replace, transform, sequence."""

    def __init__(self):
        self.text_lab = TextLabManager()
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def find_files(self, root: Path, pattern: str = "*", recursive: bool = False) -> List[Path]:
        """Finds files matching the glob pattern."""
        if recursive:
            return list(root.rglob(pattern))
        return list(root.glob(pattern))

    def calculate_renames(self, files: List[Path], search: Optional[str], replace: Optional[str], transform: Optional[str] = None) -> List[Tuple[Path, Path]]:
        """
        Calculates the new filenames based on search/replace or transform.
        Returns a list of (original_path, new_path).
        """
        renames = []
        for file in files:
            if not file.is_file():
                continue

            original_name = file.name
            new_name = original_name

            # 1. Regex/String Replace
            if search and replace is not None:
                try:
                    # Check if search is a valid regex
                    regex = re.compile(search)
                    new_name = regex.sub(replace, original_name)
                except re.error:
                    print(f"Invalid regex: {search}", file=sys.stderr)
                    return []

            # 2. Transform (e.g., lower, snake, etc.)
            if transform:
                # We apply transform to the stem (filename without extension) usually,
                # but sometimes to the whole name. Let's apply to stem by default to preserve extensions.
                stem = Path(new_name).stem
                suffix = Path(new_name).suffix

                # Use TextLabManager for transformation
                try:
                    new_stem = self.text_lab.transform(stem, transform)
                    new_name = f"{new_stem}{suffix}"
                except ValueError:
                    # If transform is unknown, skip or warn
                    pass

            if new_name != original_name:
                new_path = file.parent / new_name
                renames.append((file, new_path))

        return renames

    def apply_renames(self, renames: List[Tuple[Path, Path]], dry_run: bool = True) -> bool:
        """
        Applies the calculated renames.
        """
        if not renames:
            print("No files to rename.")
            return True

        # Check for collisions first
        destinations = [str(dest) for _, dest in renames]
        if len(destinations) != len(set(destinations)):
            print("❌ Error: Duplicate destination filenames detected. Aborting.")
            return False

        for _, dest in renames:
            # Check if destination exists AND it is NOT one of the source files being renamed
            # (Handling cyclical renames correctly requires more logic, keeping it simple: abort on collision)
            # Exception: if renaming 'a.txt' to 'a.txt' (no change) - but we filter those out in calculate_renames
            # Exception: if renaming 'a.txt' to 'b.txt' and 'b.txt' exists but is NOT being renamed.

            if dest.exists():
                # If the destination is also a source file that is being renamed, we MIGHT be okay (e.g. swap),
                # but simple rename logic usually fails here without temp files.
                # Safer to abort.
                print(f"❌ Error: Destination already exists: {dest}")
                return False

        # Print plan
        if HAS_RICH and self.console:
            table = Table(title=f"Rename Plan ({'DRY RUN' if dry_run else 'EXECUTE'})")
            table.add_column("Original", style="red")
            table.add_column("New", style="green")

            for src, dest in renames:
                table.add_row(src.name, dest.name)

            self.console.print(table)
        else:
            print(f"--- Rename Plan ({'DRY RUN' if dry_run else 'EXECUTE'}) ---")
            for src, dest in renames:
                print(f"{src.name} -> {dest.name}")

        if dry_run:
            return True

        # Execute
        try:
            for src, dest in renames:
                src.rename(dest)
            print(f"✅ Renamed {len(renames)} files.")
            return True
        except OSError as e:
            print(f"❌ Error during rename: {e}", file=sys.stderr)
            return False


def run_rename_lab_logic(args):
    """CLI handler for Rename Lab."""
    if hasattr(args, "tui") and args.tui:
        from shared.tui import AgentTUI
        print("Launching Rename Lab TUI...")
        root = Path(args.root).resolve() if getattr(args, 'root', None) else Path.cwd()
        app = AgentTUI(project_dir=root, start_tab="tab-rename")
        app.run()
        return

    manager = RenameLabManager()

    root = Path(args.root).resolve() if getattr(args, 'root', None) else Path.cwd()
    pattern = args.pattern if args.pattern else "*"

    files = manager.find_files(root, pattern, recursive=args.recursive)

    if not files:
        print(f"No files found matching '{pattern}' in {root}")
        return

    renames = manager.calculate_renames(
        files,
        search=args.search,
        replace=args.replace,
        transform=args.transform
    )

    if not renames:
        print("No files matched the criteria for renaming.")
        return

    # Dry run logic
    is_dry_run = args.dry_run
    if not is_dry_run and not args.yes:
        # If not explicit yes, force confirmation
        manager.apply_renames(renames, dry_run=True)  # Show plan first
        confirm = input("\nProceed with renaming? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return

    manager.apply_renames(renames, dry_run=is_dry_run)
