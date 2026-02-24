import os
import re
import sys
import time
import shutil
import fnmatch
from pathlib import Path
from typing import List, Optional, Generator, Tuple

class FindLabManager:
    """
    Manages advanced file finding operations (name, size, time, type).
    """

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir if root_dir else Path.cwd()

    def _parse_size(self, size_str: str) -> Tuple[str, int]:
        """
        Parses a size string like '>1M', '<10k', '500b'.
        Returns a tuple (operator, bytes).
        Operator can be '>', '<', or '='.
        """
        size_str = size_str.strip().lower()
        operator = '='
        if size_str.startswith('>'):
            operator = '>'
            size_str = size_str[1:]
        elif size_str.startswith('<'):
            operator = '<'
            size_str = size_str[1:]

        size_str = size_str.strip()

        # Parse value and unit
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([kmgt]?b?)$', size_str)
        if not match:
            raise ValueError(f"Invalid size format: {size_str}")

        value = float(match.group(1))
        unit = match.group(2)

        multiplier = 1
        if 'k' in unit: multiplier = 1024
        elif 'm' in unit: multiplier = 1024 * 1024
        elif 'g' in unit: multiplier = 1024 * 1024 * 1024
        elif 't' in unit: multiplier = 1024 * 1024 * 1024 * 1024

        return operator, int(value * multiplier)

    def _parse_time(self, time_str: str) -> Tuple[str, float]:
        """
        Parses a time string like '>1d' (older than 1 day), '<1h' (newer than 1 hour).
        Returns a tuple (operator, timestamp_threshold).
        Operator '>' means mtime < threshold (older).
        Operator '<' means mtime > threshold (newer).
        Wait, logic:
        Now = 1000.
        1 day ago = 900.
        Older than 1 day (>1d) means mtime < 900.
        Newer than 1 day (<1d) means mtime > 900.
        """
        time_str = time_str.strip().lower()
        operator = '>' # Default to older than if not specified? Or exact?
        # find -mtime +1 means older than 1 day.
        # Let's support > and < explicitly.

        if time_str.startswith('>'):
            operator = '>' # Older than
            time_str = time_str[1:]
        elif time_str.startswith('<'):
            operator = '<' # Newer than
            time_str = time_str[1:]

        match = re.match(r'^(\d+(?:\.\d+)?)\s*([smhdw]?)$', time_str)
        if not match:
            raise ValueError(f"Invalid time format: {time_str}")

        value = float(match.group(1))
        unit = match.group(2)

        seconds = 0
        if unit == 's': seconds = value
        elif unit == 'm': seconds = value * 60
        elif unit == 'h': seconds = value * 3600
        elif unit == 'd': seconds = value * 86400
        elif unit == 'w': seconds = value * 604800
        else: seconds = value

        # Default to days if no unit, similar to unix find (though find is strict)
        if not unit:
            seconds = value * 86400

        threshold = time.time() - seconds
        return operator, threshold

    def find_files(self,
                   root: Optional[Path] = None,
                   name_pattern: Optional[str] = None,
                   regex_pattern: Optional[str] = None,
                   size_filter: Optional[str] = None,
                   time_filter: Optional[str] = None,
                   type_filter: Optional[str] = None, # f, d, l
                   extensions: Optional[str] = None # comma separated
                   ) -> Generator[Path, None, None]:

        start_dir = root if root else self.root_dir
        start_dir = start_dir.resolve()

        # Prepare filters
        size_op, size_val = (None, 0)
        if size_filter:
            size_op, size_val = self._parse_size(size_filter)

        time_op, time_val = (None, 0.0)
        if time_filter:
            time_op, time_val = self._parse_time(time_filter)

        compiled_regex = None
        if regex_pattern:
            compiled_regex = re.compile(regex_pattern)

        allowed_exts = None
        if extensions:
            allowed_exts = set(e.strip().lstrip('.').lower() for e in extensions.split(','))

        # Walk
        for dirpath, dirnames, filenames in os.walk(start_dir):
            # Process directories if type_filter is 'd' or None (Any)
            if type_filter in [None, 'd']:
                for dirname in dirnames:
                    path = Path(dirpath) / dirname
                    if self._match(path, name_pattern, compiled_regex, size_op, size_val, time_op, time_val, 'd', allowed_exts):
                        yield path

            # Process files if type_filter is 'f', 'l', or None (Any)
            if type_filter in [None, 'f', 'l']:
                for filename in filenames:
                    path = Path(dirpath) / filename
                    # Determine type
                    ftype = 'f'
                    if path.is_symlink():
                        ftype = 'l'

                    if type_filter and type_filter != ftype:
                        continue

                    if self._match(path, name_pattern, compiled_regex, size_op, size_val, time_op, time_val, ftype, allowed_exts):
                        yield path

    def _match(self, path: Path, name_pattern, compiled_regex, size_op, size_val, time_op, time_val, ftype, allowed_exts):
        # Name
        if name_pattern and not fnmatch.fnmatch(path.name, name_pattern):
            return False

        # Regex
        if compiled_regex and not compiled_regex.search(str(path)):
            return False

        # Extension
        if allowed_exts:
            # Suffix includes dot, e.g. .txt
            ext = path.suffix.lstrip('.').lower()
            if ext not in allowed_exts:
                return False

        # Stat (Size & Time) - Skip for dirs unless we really want to check dir size (which is usually block size)
        # Usually size filter applies to files.
        if (size_op or time_op):
            try:
                stat = path.stat()
            except OSError:
                return False

            # Size
            if size_op:
                if ftype == 'd':
                    pass # Ignore size for dirs? Or check strict stat size? Let's check stat size.

                if size_op == '>' and not (stat.st_size > size_val): return False
                if size_op == '<' and not (stat.st_size < size_val): return False
                if size_op == '=' and not (stat.st_size == size_val): return False

            # Time (mtime)
            if time_op:
                if time_op == '>' and not (stat.st_mtime < time_val): return False # Older means timestamp is smaller
                if time_op == '<' and not (stat.st_mtime > time_val): return False # Newer means timestamp is larger

        return True

def run_find_lab_logic(args):
    """
    CLI Handler.
    """
    if hasattr(args, "tui") and args.tui:
        from shared.tui import AgentTUI
        print("Launching Find Lab TUI...")
        root = Path(args.root).resolve() if getattr(args, 'root', None) else Path.cwd()
        app = AgentTUI(project_dir=root, start_tab="tab-find")
        app.run()
        return

    root = Path(args.root).resolve() if getattr(args, 'root', None) else Path.cwd()
    manager = FindLabManager(root)

    try:
        results = manager.find_files(
            root=root,
            name_pattern=args.name,
            regex_pattern=args.regex,
            size_filter=args.size,
            time_filter=args.time,
            type_filter=args.type,
            extensions=args.ext
        )

        count = 0
        to_delete = []

        for path in results:
            count += 1
            print(path)
            if args.delete:
                to_delete.append(path)

        if count == 0:
            print("No matches found.")
            return

        # Delete logic
        if args.delete and to_delete:
            print(f"\nFound {len(to_delete)} files to delete.")
            if not args.yes:
                confirm = input("Are you sure? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("Aborted.")
                    return

            for p in to_delete:
                try:
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                    print(f"Deleted: {p}")
                except Exception as e:
                    print(f"Error deleting {p}: {e}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
