import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class NotebookLabManager:
    """
    Manages Jupyter Notebook operations: inspection, cleaning, conversion, and auditing.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def list_notebooks(self, path: Optional[Path] = None) -> List[Path]:
        """
        Lists all .ipynb files in the given path (recursive).
        """
        target_dir = path.resolve() if path else self.project_dir
        if not target_dir.exists():
            return []

        return sorted(list(target_dir.rglob("*.ipynb")))

    def inspect_notebook(self, path: Path) -> Dict[str, Any]:
        """
        Returns metadata and statistics about the notebook.
        """
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {"error": f"Invalid notebook format: {e}"}

        metadata = data.get("metadata", {})
        kernelspec = metadata.get("kernelspec", {})
        language_info = metadata.get("language_info", {})

        cells = data.get("cells", [])
        stats = {
            "code": 0,
            "markdown": 0,
            "raw": 0,
            "total": len(cells)
        }

        for cell in cells:
            ctype = cell.get("cell_type", "unknown")
            if ctype in stats:
                stats[ctype] += 1

        return {
            "kernel": kernelspec.get("display_name", "Unknown"),
            "language": language_info.get("name", "Unknown"),
            "version": language_info.get("version", "Unknown"),
            "cells": stats,
            "nbformat": f"{data.get('nbformat', '?')}.{data.get('nbformat_minor', '?')}"
        }

    def clean_notebook(self, path: Path, dry_run: bool = False) -> bool:
        """
        Clears outputs and execution counts from code cells.
        """
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading notebook: {e}", file=sys.stderr)
            return False

        changed = False
        cells = data.get("cells", [])

        for cell in cells:
            if cell.get("cell_type") == "code":
                if cell.get("outputs"):
                    cell["outputs"] = []
                    changed = True
                if cell.get("execution_count") is not None:
                    cell["execution_count"] = None
                    changed = True

        if changed and not dry_run:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=1) # Standardize indent
                return True
            except Exception as e:
                print(f"Error writing notebook: {e}", file=sys.stderr)
                return False

        return changed

    def convert_to_script(self, path: Path, output: Optional[Path] = None) -> Path:
        """
        Converts notebook code cells to a Python script.
        """
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error reading notebook: {e}")

        cells = data.get("cells", [])
        script_lines = []

        for i, cell in enumerate(cells):
            if cell.get("cell_type") == "code":
                source = cell.get("source", [])
                if isinstance(source, str):
                    source = source.splitlines(keepends=True)

                script_lines.append(f"\n# %% [cell {i}]\n")

                for line in source:
                    # Comment out magic commands
                    if line.strip().startswith(("!", "%")):
                        script_lines.append(f"# {line}")
                    else:
                        script_lines.append(line)

            elif cell.get("cell_type") == "markdown":
                # Optionally verify markdown as comments?
                pass

        content = "".join(script_lines)

        if not output:
            output = path.with_suffix(".py")

        output.write_text(content, encoding="utf-8")
        return output

    def audit_notebook(self, path: Path) -> List[Dict[str, Any]]:
        """
        Checks notebook for issues:
        - Large output size
        - Out-of-order execution
        - Potential secrets
        """
        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Read raw text for size check first?
                # No, let's load json
                f.seek(0)
                data = json.load(f)
        except Exception as e:
            return [{"type": "Error", "message": str(e)}]

        issues = []
        cells = data.get("cells", [])

        last_exec_count = -1
        is_linear = True

        # Secret patterns (naive)
        secret_patterns = [
            re.compile(r"(?i)(api_key|secret|password|token)\s*=\s*['\"][\w-]{8,}['\"]"),
            re.compile(r"(?i)sk-[\w-]{20,}") # OpenAI key style
        ]

        for i, cell in enumerate(cells):
            if cell.get("cell_type") == "code":
                # Check Execution Order
                count = cell.get("execution_count")
                if count is not None:
                    if isinstance(count, int):
                        if count <= last_exec_count:
                            is_linear = False
                        last_exec_count = count

                # Check Outputs Size
                outputs = cell.get("outputs", [])
                for out in outputs:
                    # Check for large text/data
                    if "text" in out:
                        text_content = "".join(out["text"])
                        if len(text_content) > 10000: # 10KB text output
                            issues.append({
                                "type": "Large Output",
                                "cell": i,
                                "message": f"Large text output ({len(text_content)} chars)"
                            })
                    # Check for large image data (base64)
                    if "data" in out:
                        for mime, content in out["data"].items():
                            if isinstance(content, str) and len(content) > 100000: # 100KB data
                                issues.append({
                                    "type": "Large Output",
                                    "cell": i,
                                    "message": f"Large data output for {mime} ({len(content)} chars)"
                                })

                # Check Secrets in Source
                source = "".join(cell.get("source", []))
                for pattern in secret_patterns:
                    if pattern.search(source):
                        issues.append({
                            "type": "Security Risk",
                            "cell": i,
                            "message": "Potential secret detected in code."
                        })

        if not is_linear:
            issues.append({
                "type": "Execution Order",
                "cell": "Global",
                "message": "Notebook execution counts are non-linear or out of order."
            })

        return issues


def run_notebook_lab_logic(args):
    """
    CLI Entry point for Notebook Lab.
    """
    project_dir = args.project_dir.resolve()
    manager = NotebookLabManager(project_dir)

    if args.action == "list":
        notebooks = manager.list_notebooks()
        if not notebooks:
            print("No notebooks found.")
            sys.exit(0)

        print(f"--- Notebooks ({len(notebooks)}) ---")
        for nb in notebooks:
            try:
                rel_path = nb.relative_to(project_dir)
            except ValueError:
                rel_path = nb
            print(f"  {rel_path}")
        sys.exit(0)

    elif args.action == "inspect":
        path = Path(args.file)
        if not path.is_absolute():
            path = project_dir / path

        info = manager.inspect_notebook(path)
        if "error" in info:
            print(f"❌ {info['error']}")
            sys.exit(1)

        print(f"--- Inspecting: {path.name} ---")
        print(f"Kernel:   {info['kernel']}")
        print(f"Language: {info['language']} {info['version']}")
        print(f"Format:   v{info['nbformat']}")
        print("Cells:")
        for k, v in info['cells'].items():
            print(f"  {k.capitalize()}: {v}")
        sys.exit(0)

    elif args.action == "clean":
        path = Path(args.file)
        if not path.is_absolute():
            path = project_dir / path

        if manager.clean_notebook(path, dry_run=args.dry_run):
            if args.dry_run:
                print(f"ℹ️  Notebook {path.name} would be cleaned (outputs removed).")
            else:
                print(f"✅ Notebook {path.name} cleaned.")
        else:
            print(f"ℹ️  Notebook {path.name} is already clean or error occurred.")
        sys.exit(0)

    elif args.action == "convert":
        path = Path(args.file)
        if not path.is_absolute():
            path = project_dir / path

        try:
            out = manager.convert_to_script(path)
            print(f"✅ Converted to {out}")
        except Exception as e:
            print(f"❌ Error converting: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif args.action == "audit":
        path = Path(args.file)
        if not path.is_absolute():
            path = project_dir / path

        issues = manager.audit_notebook(path)
        if not issues:
            print("✅ No issues found.")
            sys.exit(0)

        print(f"⚠️  Found {len(issues)} issues in {path.name}:")
        for issue in issues:
            cell_info = f" (Cell {issue['cell']})" if issue['cell'] != "Global" else ""
            print(f"  [{issue['type']}] {issue['message']}{cell_info}")
        sys.exit(1) # Exit with error code if issues found

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
