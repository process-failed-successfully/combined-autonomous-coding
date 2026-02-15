import sys
import json
import yaml
import difflib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

try:
    from rich.console import Console
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from PIL import Image, ImageChops, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

class DiffLabManager:
    """
    Manages smart file comparison for various formats.
    """
    def __init__(self):
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def compare_files(self, file1: Path, file2: Path, ftype: str = None, output: Path = None):
        """
        Main entry point for comparison.
        """
        if not file1.exists():
            print(f"❌ File not found: {file1}")
            return
        if not file2.exists():
            print(f"❌ File not found: {file2}")
            return

        # Auto-detect type
        if not ftype:
            suffix1 = file1.suffix.lower()
            suffix2 = file2.suffix.lower()

            if suffix1 in ['.json'] and suffix2 in ['.json']:
                ftype = 'json'
            elif suffix1 in ['.yaml', '.yml'] and suffix2 in ['.yaml', '.yml']:
                ftype = 'yaml'
            elif suffix1 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] and suffix2 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                ftype = 'image'
            else:
                ftype = 'text'

        print(f"Comparing {file1.name} and {file2.name} as {ftype.upper()}...")

        if ftype == 'json':
            self._compare_json(file1, file2)
        elif ftype == 'yaml':
            self._compare_yaml(file1, file2)
        elif ftype == 'image':
            self._compare_image(file1, file2, output)
        else:
            self._compare_text(file1, file2)

    def _compare_text(self, file1: Path, file2: Path):
        """
        Standard text comparison using difflib.
        """
        try:
            with open(file1, 'r', encoding='utf-8', errors='replace') as f1, \
                 open(file2, 'r', encoding='utf-8', errors='replace') as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()
        except Exception as e:
            print(f"Error reading files: {e}")
            return

        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=str(file1),
            tofile=str(file2)
        ))

        if not diff:
            print("✅ Files are identical.")
            return

        if HAS_RICH and self.console:
            # Simple syntax highlighting for diff
            diff_text = "".join(diff)
            syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            for line in diff:
                print(line, end="")

    def _compare_json(self, file1: Path, file2: Path):
        """
        Semantic JSON comparison.
        """
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                data1 = json.load(f)
            with open(file2, 'r', encoding='utf-8') as f:
                data2 = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print("Falling back to text comparison.")
            self._compare_text(file1, file2)
            return

        self._compare_structure(data1, data2)

    def _compare_yaml(self, file1: Path, file2: Path):
        """
        Semantic YAML comparison.
        """
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                data1 = yaml.safe_load(f)
            with open(file2, 'r', encoding='utf-8') as f:
                data2 = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            print("Falling back to text comparison.")
            self._compare_text(file1, file2)
            return

        self._compare_structure(data1, data2)

    def _compare_structure(self, data1: Any, data2: Any):
        """
        Recursive semantic comparison.
        """
        diffs = self._diff_recursive(data1, data2)

        if not diffs:
            print("✅ Structures are semantically identical.")
            return

        if HAS_RICH and self.console:
            table = Table(title="Structural Differences", box=box.SIMPLE)
            table.add_column("Path", style="cyan")
            table.add_column("Change", style="bold")
            table.add_column("Old Value", style="red")
            table.add_column("New Value", style="green")

            for d in diffs:
                path = "root" + d['path']
                old_val = json.dumps(d.get('old'), default=str) if 'old' in d else "N/A"
                new_val = json.dumps(d.get('new'), default=str) if 'new' in d else "N/A"

                # Truncate long values
                if len(old_val) > 30: old_val = old_val[:27] + "..."
                if len(new_val) > 30: new_val = new_val[:27] + "..."

                table.add_row(path, d['type'], old_val, new_val)

            self.console.print(table)
        else:
            for d in diffs:
                path = "root" + d['path']
                print(f"{path}: {d['type']} | Old: {d.get('old')} | New: {d.get('new')}")

    def _diff_recursive(self, d1, d2, path="") -> List[Dict]:
        """
        Compare two python objects (dicts, lists, primitives) and return a list of differences.
        """
        diffs = []

        if isinstance(d1, dict) and isinstance(d2, dict):
            keys1 = set(d1.keys())
            keys2 = set(d2.keys())

            # Added
            for k in keys2 - keys1:
                diffs.append({"type": "ADDED", "path": f"{path}[{repr(k)}]", "new": d2[k]})

            # Removed
            for k in keys1 - keys2:
                diffs.append({"type": "REMOVED", "path": f"{path}[{repr(k)}]", "old": d1[k]})

            # Common
            for k in keys1 & keys2:
                diffs.extend(self._diff_recursive(d1[k], d2[k], f"{path}[{repr(k)}]"))

        elif isinstance(d1, list) and isinstance(d2, list):
            # Simple list comparison by index for now (order matters)
            # Improving this to ignore order for lists of dicts would be 'smarter' but complex without IDs
            len1 = len(d1)
            len2 = len(d2)

            for i in range(min(len1, len2)):
                diffs.extend(self._diff_recursive(d1[i], d2[i], f"{path}[{i}]"))

            if len2 > len1:
                for i in range(len1, len2):
                    diffs.append({"type": "ADDED_ITEM", "path": f"{path}[{i}]", "new": d2[i]})
            elif len1 > len2:
                for i in range(len2, len1):
                    diffs.append({"type": "REMOVED_ITEM", "path": f"{path}[{i}]", "old": d1[i]})

        else:
            if d1 != d2:
                diffs.append({"type": "MODIFIED", "path": path, "old": d1, "new": d2})

        return diffs

    def _compare_image(self, file1: Path, file2: Path, output: Path = None):
        """
        Visual image comparison using Pillow.
        """
        if not HAS_PILLOW:
            print("❌ Pillow library not installed. Cannot compare images.")
            return

        try:
            img1 = Image.open(file1)
            img2 = Image.open(file2)
        except Exception as e:
            print(f"Error opening images: {e}")
            return

        if img1.size != img2.size or img1.mode != img2.mode:
            print("⚠️  Images differ in properties:")
            print(f"  {file1.name}: {img1.format} {img1.size} {img1.mode}")
            print(f"  {file2.name}: {img2.format} {img2.size} {img2.mode}")
            print("Cannot perform pixel-by-pixel diff overlay.")
            return

        # Compute difference
        diff = ImageChops.difference(img1, img2)

        # Check if identical
        if not diff.getbbox():
            print("✅ Images are pixel-identical.")
            return

        print("❌ Images differ.")

        if output:
            # Invert diff to make it visible (black -> white)
            try:
                from PIL import ImageOps
                diff = ImageOps.invert(diff)
            except Exception:
                pass

            diff.save(output)
            print(f"Diff image saved to: {output}")
        else:
            print("Use --output to save the visual difference map.")


def run_diff_lab_logic(args):
    """
    CLI entry point for Diff Lab.
    """
    manager = DiffLabManager()

    file1 = Path(args.file1).resolve()
    file2 = Path(args.file2).resolve()
    output = Path(args.output).resolve() if args.output else None

    manager.compare_files(file1, file2, ftype=args.type, output=output)
    sys.exit(0)
