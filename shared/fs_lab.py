import os
import sys
import shutil
import hashlib
import fnmatch
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

try:
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.progress import track
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class FsLabManager:
    """
    Manages advanced file system operations: find, info, dedup, usage, clean, shred.
    """

    def __init__(self, console: Optional['Console'] = None):
        if HAS_RICH and console is None:
            self.console = Console()
        else:
            self.console = console

    def _format_size(self, size: int) -> str:
        """Converts bytes to human-readable strings."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _parse_size(self, size_str: str) -> int:
        """Parses size string (e.g. 10MB, 1g) to bytes."""
        size_str = size_str.upper().strip()
        units = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}

        # Check if last char is a unit
        unit = 1
        # Check 2-char suffix first (e.g. KB, MB)
        if len(size_str) > 1 and size_str[-2:] in [u+'B' for u in units]:
            unit = units[size_str[-2]]
            val = float(size_str[:-2])
        # Check 1-char suffix (e.g. K, M)
        elif size_str[-1] in units:
            unit = units[size_str[-1]]
            val = float(size_str[:-1])
        else:
            val = float(size_str)

        return int(val * unit)

    def _parse_time(self, time_str: str) -> float:
        """Parses time string (e.g. 1d, 2h) to seconds."""
        time_str = time_str.lower().strip()
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}

        unit = 1
        if time_str[-1] in units:
            unit = units[time_str[-1]]
            val = float(time_str[:-1])
        else:
            val = float(time_str)

        return val * unit

    def get_info(self, path: Path) -> Dict[str, Any]:
        """Returns detailed metadata for a file."""
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")

        stat = path.stat()
        info = {
            "name": path.name,
            "path": str(path.resolve()),
            "type": "Dir" if path.is_dir() else "File",
            "size": stat.st_size,
            "formatted_size": self._format_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "owner": stat.st_uid, # Resolving to name requires 'pwd' module which might not be cross-platform safe
            "group": stat.st_gid,
        }

        # Basic MIME type guess (extension based)
        import mimetypes
        mime, encoding = mimetypes.guess_type(path)
        info["mime_type"] = mime or "unknown"
        info["encoding"] = encoding

        if path.is_file():
            # Calculate SHA256 (only if file < 100MB to be fast)
            if stat.st_size < 100 * 1024 * 1024:
                try:
                    hasher = hashlib.sha256()
                    with open(path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    info["sha256"] = hasher.hexdigest()
                except Exception:
                    info["sha256"] = "Error reading file"
            else:
                info["sha256"] = "Skipped (too large)"

        return info

    def find(self, root: Path, name: str = "*", size: str = None, mtime: str = None, ftype: str = None, content: str = None) -> List[Path]:
        """
        Finds files based on criteria.
        size: >10M, <1k
        mtime: >1d (older than 1 day), <2h (newer than 2 hours)
        ftype: f (file), d (dir)
        """
        results = []
        root = root.resolve()

        # Parse size constraint
        size_op = None
        size_val = 0
        if size:
            if size.startswith('>'):
                size_op = '>'
                size_val = self._parse_size(size[1:])
            elif size.startswith('<'):
                size_op = '<'
                size_val = self._parse_size(size[1:])
            else:
                size_op = '='
                size_val = self._parse_size(size)

        # Parse time constraint (mtime)
        time_op = None
        time_val = 0
        now = time.time()
        if mtime:
            if mtime.startswith('>'): # Older than
                time_op = '>'
                time_val = self._parse_time(mtime[1:])
            elif mtime.startswith('<'): # Newer than
                time_op = '<'
                time_val = self._parse_time(mtime[1:])
            else:
                # Exact match isn't very useful for time, assuming older than as default? No, let's treat as 'older than' if no op
                time_op = '>'
                time_val = self._parse_time(mtime)

        # Content regex
        content_re = None
        if content:
            content_re = re.compile(content)

        for p in root.rglob(name):
            try:
                # Type check
                if ftype:
                    if ftype == 'f' and not p.is_file(): continue
                    if ftype == 'd' and not p.is_dir(): continue

                stat = p.stat()

                # Size check
                if size_op:
                    if size_op == '>' and stat.st_size <= size_val: continue
                    if size_op == '<' and stat.st_size >= size_val: continue
                    if size_op == '=' and stat.st_size != size_val: continue

                # Time check
                if time_op:
                    age = now - stat.st_mtime
                    if time_op == '>' and age <= time_val: continue
                    if time_op == '<' and age >= time_val: continue

                # Content check
                if content_re:
                    if not p.is_file():
                        continue

                    try:
                        # Read first few KB to guess encoding or check for binary
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            # Read in chunks to avoid loading huge files
                            found = False
                            for line in f:
                                if content_re.search(line):
                                    found = True
                                    break
                            if not found: continue
                    except Exception:
                        continue

                results.append(p)

            except OSError:
                continue

        return results

    def dedup(self, root: Path, delete: bool = False, dry_run: bool = True) -> Dict[str, List[Path]]:
        """
        Finds duplicates by SHA256 hash.
        Returns a dict of hash -> list of paths.
        """
        hashes = {} # hash -> list of paths
        files_by_size = {} # size -> list of paths (optimization)

        # 1. Group by size first
        for p in root.rglob("*"):
            if p.is_file() and not p.is_symlink():
                try:
                    s = p.stat().st_size
                    if s not in files_by_size:
                        files_by_size[s] = []
                    files_by_size[s].append(p)
                except OSError:
                    continue

        # 2. Hash files with same size
        for size, paths in files_by_size.items():
            if len(paths) < 2: continue

            for p in paths:
                try:
                    hasher = hashlib.sha256()
                    with open(p, 'rb') as f:
                        # Read only first 4k first as a quick check?
                        # No, full hash for correctness.
                        for chunk in iter(lambda: f.read(8192), b""):
                            hasher.update(chunk)
                    h = hasher.hexdigest()

                    if h not in hashes:
                        hashes[h] = []
                    hashes[h].append(p)
                except OSError:
                    continue

        # Filter out unique files
        duplicates = {h: p for h, p in hashes.items() if len(p) > 1}

        # Delete if requested
        if delete:
            for h, paths in duplicates.items():
                # Keep the first one (shortest path or alphabetical)
                # Let's keep the one with shortest path length (likely closer to root)
                paths.sort(key=lambda x: (len(str(x)), str(x)))
                to_keep = paths[0]
                to_delete = paths[1:]

                for p in to_delete:
                    if dry_run:
                        if HAS_RICH and self.console:
                            self.console.print(f"[yellow]Would delete:[/yellow] {p} (duplicate of {to_keep})")
                        else:
                            print(f"Would delete: {p} (duplicate of {to_keep})")
                    else:
                        try:
                            p.unlink()
                            if HAS_RICH and self.console:
                                self.console.print(f"[green]Deleted:[/green] {p}")
                            else:
                                print(f"Deleted: {p}")
                        except OSError as e:
                            print(f"Error deleting {p}: {e}")

        return duplicates

    def clean(self, root: Path, dry_run: bool = True) -> Dict[str, int]:
        """
        Cleans temporary files and empty directories.
        """
        stats = {"files": 0, "dirs": 0, "space": 0}
        patterns = ["__pycache__", ".DS_Store", "Thumbs.db", "*.tmp", "*.log", "*.bak", "*.swp"]

        # 1. Clean files based on patterns
        for pattern in patterns:
            for p in root.rglob(pattern):
                try:
                    if p.is_dir() and pattern == "__pycache__":
                        # Special handling for directories matching pattern
                        size = 0 # Directories effectively 0 size usually
                        if dry_run:
                            print(f"Would remove dir: {p}")
                        else:
                            shutil.rmtree(p)
                            print(f"Removed dir: {p}")
                        stats["dirs"] += 1
                    elif p.is_file():
                        size = p.stat().st_size
                        if dry_run:
                            print(f"Would remove file: {p} ({self._format_size(size)})")
                        else:
                            p.unlink()
                            print(f"Removed file: {p}")
                        stats["files"] += 1
                        stats["space"] += size
                except OSError:
                    continue

        # 2. Clean empty directories
        # os.walk bottom-up
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            p = Path(dirpath)
            if p == root: continue # Don't delete root
            try:
                # check if empty (might have become empty after file deletion)
                if not any(p.iterdir()):
                    if dry_run:
                        print(f"Would remove empty dir: {p}")
                    else:
                        p.rmdir()
                        print(f"Removed empty dir: {p}")
                    stats["dirs"] += 1
            except OSError:
                continue

        return stats

    def shred(self, path: Path, passes: int = 3) -> bool:
        """
        Securely deletes a file.
        """
        if not path.exists() or not path.is_file():
            print(f"File {path} not found or is not a file.")
            return False

        size = path.stat().st_size

        try:
            with open(path, 'wb') as f:
                for pass_num in range(passes):
                    # Random data
                    f.seek(0)
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())

                # Final pass: Zeros
                f.seek(0)
                f.write(b'\x00' * size)
                f.flush()
                os.fsync(f.fileno())

            path.unlink()
            return True
        except OSError as e:
            print(f"Error shredding file: {e}")
            return False

    def usage(self, root: Path, depth: int = 1) -> None:
        """
        Prints disk usage tree.
        """
        if not HAS_RICH:
            print("Rich library required for usage tree.")
            return

        def build_tree(path: Path, tree_node: Tree, current_depth: int):
            if current_depth > depth:
                return 0

            total_size = 0
            try:
                # Separate dirs and files
                entries = sorted(list(path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))

                for entry in entries:
                    try:
                        if entry.is_file():
                            size = entry.stat().st_size
                            total_size += size
                            if current_depth < depth:
                                tree_node.add(f"📄 {entry.name} ({self._format_size(size)})")
                        elif entry.is_dir():
                            # Create a branch
                            branch = tree_node.add(f"📁 {entry.name} ...")
                            size = build_tree(entry, branch, current_depth + 1)
                            total_size += size
                            # Update branch label with size
                            branch.label = f"📁 {entry.name} ({self._format_size(size)})"
                    except OSError:
                        continue
            except OSError:
                pass

            return total_size

        root_tree = Tree(f"📁 {root.name}")
        total = build_tree(root, root_tree, 0)
        root_tree.label = f"📁 {root.name} ({self._format_size(total)})"

        self.console.print(root_tree)


def run_fs_lab_logic(args):
    """
    CLI Entry point for Fs Lab.
    """
    manager = FsLabManager()

    if args.action == "info":
        try:
            path = Path(args.path).resolve()
            info = manager.get_info(path)

            if HAS_RICH:
                table = Table(title=f"File Info: {info['name']}")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                for k, v in info.items():
                    table.add_row(k.replace('_', ' ').title(), str(v))
                manager.console.print(table)
            else:
                for k, v in info.items():
                    print(f"{k}: {v}")

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "find":
        root = Path(args.root).resolve() if args.root else Path(".").resolve()
        results = manager.find(
            root,
            name=args.name,
            size=args.size,
            mtime=args.mtime,
            ftype=args.type,
            content=args.content
        )

        print(f"Found {len(results)} matches in {root}:")
        for p in results:
            print(f"  {p}")

    elif args.action == "dedup":
        root = Path(args.root).resolve() if args.root else Path(".").resolve()
        duplicates = manager.dedup(root, delete=args.delete, dry_run=not args.force)

        if not args.delete:
            count = 0
            for h, paths in duplicates.items():
                print(f"Duplicate Group ({h[:8]}...):")
                for p in paths:
                    print(f"  - {p}")
                count += len(paths) - 1
            print(f"\nFound {len(duplicates)} groups with duplicates (approx {count} redundant files).")

    elif args.action == "clean":
        root = Path(args.root).resolve() if args.root else Path(".").resolve()
        stats = manager.clean(root, dry_run=not args.force)

        if not args.force:
            print("\n[Dry Run] Use --force to actually delete.")

        print(f"\nSummary:")
        print(f"  Files: {stats['files']}")
        print(f"  Dirs:  {stats['dirs']}")
        print(f"  Space: {manager._format_size(stats['space'])}")

    elif args.action == "shred":
        path = Path(args.path).resolve()
        if not args.force:
            confirm = input(f"Are you sure you want to securely delete {path}? [y/N]: ").lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        if manager.shred(path, passes=args.passes):
            print(f"✅ Securely deleted {path}")
        else:
            sys.exit(1)

    elif args.action == "usage":
        root = Path(args.root).resolve() if args.root else Path(".").resolve()
        manager.usage(root, depth=args.depth)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
