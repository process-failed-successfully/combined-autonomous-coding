import ast
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

class DocsGenerator:
    """
    Generates Markdown documentation from Python source code using AST.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def scan(self, source_dir: Path) -> Dict[str, Any]:
        """
        Scans a directory for Python files and extracts documentation.
        Returns a nested dictionary representing the module structure.
        """
        structure = {}
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(source_dir)
                    module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')

                    try:
                        doc_info = self._parse_file(file_path)
                        if doc_info:
                            structure[module_name] = doc_info
                    except Exception as e:
                        print(f"Warning: Failed to parse {file_path}: {e}", file=sys.stderr)
        return structure

    def _parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parses a single Python file using AST and extracts docstrings.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception:
            return None

        module_doc = ast.get_docstring(tree)
        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [],
                    "bases": [b.id for b in node.bases if isinstance(b, ast.Name)]
                }
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            "name": item.name,
                            "docstring": ast.get_docstring(item),
                            "args": [a.arg for a in item.args.args if a.arg != 'self']
                        }
                        class_info["methods"].append(method_info)
                classes.append(class_info)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "args": [a.arg for a in node.args.args]
                }
                functions.append(func_info)

        return {
            "path": file_path,
            "docstring": module_doc,
            "classes": classes,
            "functions": functions
        }

    def generate(self, source_dir: Path, output_dir: Path):
        """
        Generates Markdown documentation for the source directory.
        """
        if not source_dir.exists():
            print(f"Error: Source directory {source_dir} does not exist.", file=sys.stderr)
            return False

        structure = self.scan(source_dir)
        if not structure:
            print("No Python files found to document.")
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate module docs
        for module_name, info in structure.items():
            # Create subdirectories if needed (e.g. shared.utils -> shared/utils.md)
            # Actually, flattened structure or nested?
            # Let's keep it simple: flattened or mirroring structure.
            # Mirroring:
            rel_path = info["path"].relative_to(source_dir)
            doc_path = output_dir / rel_path.with_suffix('.md')
            doc_path.parent.mkdir(parents=True, exist_ok=True)

            self._write_module_doc(module_name, info, doc_path)

        # Generate Index
        self._write_index(structure, output_dir)
        return True

    def _write_module_doc(self, module_name: str, info: Dict[str, Any], output_path: Path):
        """
        Writes documentation for a single module.
        """
        lines = []
        lines.append(f"# Module: `{module_name}`")
        lines.append("")

        if info["docstring"]:
            lines.append(info["docstring"])
            lines.append("")

        if info["classes"]:
            lines.append("## Classes")
            lines.append("")
            for cls in info["classes"]:
                bases = f"({', '.join(cls['bases'])})" if cls['bases'] else ""
                lines.append(f"### `class {cls['name']}{bases}`")
                if cls["docstring"]:
                    lines.append(f"\n{cls['docstring']}\n")

                if cls["methods"]:
                    lines.append("#### Methods")
                    for method in cls["methods"]:
                        args = ", ".join(method["args"])
                        lines.append(f"- **`{method['name']}({args})`**")
                        if method["docstring"]:
                             # Indent docstring slightly or just print first line
                             summary = method["docstring"].split('\n')[0]
                             lines.append(f"  - {summary}")
                lines.append("")

        if info["functions"]:
            lines.append("## Functions")
            lines.append("")
            for func in info["functions"]:
                args = ", ".join(func["args"])
                lines.append(f"### `{func['name']}({args})`")
                if func["docstring"]:
                    lines.append(f"\n{func['docstring']}\n")
                lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _write_index(self, structure: Dict[str, Any], output_dir: Path):
        """
        Writes the index/README file.
        """
        index_path = output_dir / "README.md"
        lines = ["# API Documentation", "", "## Modules", ""]

        # Sort modules
        sorted_modules = sorted(structure.keys())

        for module in sorted_modules:
            # Relative link
            # If module is shared.utils, path is shared/utils.md
            # We need link relative to output_dir root (README.md location)
            file_path = structure[module]["path"]
            # Assume we generated mirrored structure in output_dir
            # We need to construct the relative path for the link
            # e.g. module "shared.utils" -> "shared/utils.md"
            link_path = module.replace('.', '/') + ".md"
            lines.append(f"- [{module}]({link_path})")

        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def clean(self, output_dir: Path):
        """
        Removes the generated documentation directory.
        """
        if output_dir.exists():
            shutil.rmtree(output_dir)
            return True
        return False

def run_docs_lab_logic(args):
    """
    CLI Handler for Docs Lab.
    """
    project_dir = args.project_dir.resolve()
    generator = DocsGenerator(project_dir)

    if args.action == "generate":
        source_dir = Path(args.source).resolve() if args.source else project_dir
        output_dir = Path(args.output).resolve() if args.output else project_dir / "docs" / "api"

        print(f"Generating docs from {source_dir} to {output_dir}...")
        if generator.generate(source_dir, output_dir):
            print(f"✅ Documentation generated in {output_dir}")
        else:
            sys.exit(1)

    elif args.action == "clean":
        output_dir = Path(args.output).resolve() if args.output else project_dir / "docs" / "api"
        print(f"Cleaning {output_dir}...")
        if generator.clean(output_dir):
             print(f"✅ Removed {output_dir}")
        else:
             print(f"Directory {output_dir} does not exist.")

    sys.exit(0)
