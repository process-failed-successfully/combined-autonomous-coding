"""
Code Complexity Analyzer
========================

Calculates Cyclomatic Complexity for Python files using the AST.
"""

import ast
import os
from pathlib import Path
import shutil
import subprocess
import concurrent.futures

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1  # Base complexity is 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        # Each except handler adds a path
        self.complexity += len(node.handlers)
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # Each boolean operator (and/or) adds a path
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    # Stop recursion at nested function definitions
    def visit_FunctionDef(self, node):
        pass

    def visit_AsyncFunctionDef(self, node):
        pass

    # Note: We don't increment for function definitions themselves if we are analyzing the function body,
    # but if we are analyzing a file, we might just look at functions.
    # The standard way is to calculate complexity PER FUNCTION.

class FunctionComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node):
        visitor = ComplexityVisitor()
        # Visit the body of the function
        for child in node.body:
            visitor.visit(child)

        self.functions.append({
            "name": node.name,
            "complexity": visitor.complexity,
            "lineno": node.lineno
        })
        # We don't recurse generic_visit(node) here because we handled the body.
        # However, we DO want to find nested functions.
        # But if we recurse, we might double count or confuse context.
        # A simple approach: standard complexity tools usually just look at top-level or nested functions independently.

        # To handle nested functions, we should conceptually visit the body again looking for FunctionDefs?
        # Actually, if we just run generic_visit(node), it will hit nested FunctionDefs.
        # But our `ComplexityVisitor` shouldn't increment for nested FunctionDefs, it should only calculate logic flow.
        # The `ComplexityVisitor` above treats everything equally.

        # Let's support nested functions by traversing normally.
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        visitor = ComplexityVisitor()
        for child in node.body:
            visitor.visit(child)

        self.functions.append({
            "name": node.name,
            "complexity": visitor.complexity,
            "lineno": node.lineno
        })
        self.generic_visit(node)

def calculate_complexity(source_code: str):
    """Calculates complexity for all functions in the source code."""
    try:
        tree = ast.parse(source_code)
        visitor = FunctionComplexityVisitor()
        visitor.visit(tree)
        return visitor.functions
    except SyntaxError as e:
        print(f"DEBUG: SyntaxError in file: {e}")
        return []

def get_python_files(project_dir: Path):
    """Gets all Python files respecting .gitignore."""
    project_dir = project_dir.resolve()
    git_path = shutil.which("git")

    if git_path and (project_dir / ".git").is_dir():
        try:
            # Use git ls-files to get tracked and untracked files (respecting .gitignore)
            # -c: cached (tracked)
            # -o: others (untracked)
            # --exclude-standard: respect .gitignore for untracked files
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "ls-files", "-c", "-o", "--exclude-standard", "*.py"],
                capture_output=True, text=True, check=True
            )
            files = [project_dir / f for f in result.stdout.splitlines() if f]
            # Remove duplicates (in case a file is listed twice, though ls-files handles this well usually)
            return list(set(files))
        except subprocess.CalledProcessError:
            pass

    # Fallback to os.walk if git fails or not a repo
    py_files = []
    for root, _, filenames in os.walk(project_dir):
        if ".git" in root or "__pycache__" in root or ".venv" in root or "node_modules" in root:
            continue
        for name in filenames:
            if name.endswith(".py"):
                py_files.append(Path(root) / name)
    return py_files

def analyze_project_complexity(project_dir: Path):
    """Analyzes complexity for the entire project."""
    project_dir = project_dir.resolve()
    files = get_python_files(project_dir)
    results = []

    def process_file(file_path):
        if not file_path.exists():
            return []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            functions = calculate_complexity(content)
            file_results = []
            for func in functions:
                file_results.append({
                    "file": str(file_path.relative_to(project_dir)),
                    "function": func["name"],
                    "complexity": func["complexity"],
                    "lineno": func["lineno"]
                })
            return file_results
        except Exception:
            # Ignore read errors
            return []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(process_file, f): f for f in files}
        for future in concurrent.futures.as_completed(future_to_file):
            results.extend(future.result())

    return results

def _run_analytics_complexity_logic(project_dir: Path):
    """Displays the complexity analysis."""
    print(f"--- Code Complexity Analysis: {project_dir.resolve().name} ---")
    print("Scanning Python files...\n")

    results = analyze_project_complexity(project_dir)

    if not results:
        print("No Python functions found.")
        return

    # Calculate stats
    total_complexity = sum(r["complexity"] for r in results)
    avg_complexity = total_complexity / len(results)
    max_complexity = max(r["complexity"] for r in results)

    # Sort by complexity descending
    sorted_results = sorted(results, key=lambda x: x["complexity"], reverse=True)

    print(f"Total Functions:    {len(results)}")
    print(f"Average Complexity: {avg_complexity:.2f}")
    print(f"Max Complexity:     {max_complexity}")

    # Risk assessment
    # A complexity > 10 is often considered a risk.
    high_risk = [r for r in results if r["complexity"] > 10]

    print("\n[ Top Complex Functions ]")
    header = f"{'Complexity':<10} | {'File':<40} | {'Function'}"
    print(header)
    print("-" * len(header))

    for r in sorted_results[:10]:
        file_display = r["file"]
        if len(file_display) > 38:
            file_display = "..." + file_display[-35:]
        print(f"{r['complexity']:<10} | {file_display:<40} | {r['function']}:{r['lineno']}")

    if high_risk:
        percentage = (len(high_risk) / len(results)) * 100
        print(f"\n⚠️  {len(high_risk)} functions ({percentage:.1f}%) have high complexity (> 10).")
        print("   Consider refactoring these functions to improve maintainability.")
    else:
        print("\n✅ All functions have acceptable complexity (<= 10).")
