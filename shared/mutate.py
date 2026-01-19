import ast
import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import List, Any, Optional
from rich.console import Console
from rich.table import Table

console = Console()

class Mutation:
    def __init__(self, node: ast.AST, mutation_op: Any, lineno: int, col_offset: int, description: str, node_type: type):
        self.node_class = node.__class__
        self.mutation_op = mutation_op
        self.lineno = lineno
        self.col_offset = col_offset
        self.description = description
        self.node_type = node_type

    def __repr__(self):
        return f"Line {self.lineno}: {self.description}"

class MutationVisitor(ast.NodeVisitor):
    def __init__(self):
        self.mutations: List[Mutation] = []

    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.op, ast.Add):
            self.mutations.append(Mutation(node, ast.Sub(), node.lineno, node.col_offset, "Change + to -", ast.BinOp))
        elif isinstance(node.op, ast.Sub):
            self.mutations.append(Mutation(node, ast.Add(), node.lineno, node.col_offset, "Change - to +", ast.BinOp))
        elif isinstance(node.op, ast.Mult):
            self.mutations.append(Mutation(node, ast.Div(), node.lineno, node.col_offset, "Change * to /", ast.BinOp))
        elif isinstance(node.op, ast.Div):
            self.mutations.append(Mutation(node, ast.Mult(), node.lineno, node.col_offset, "Change / to *", ast.BinOp))
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        # Only mutate the first op for simplicity
        if node.ops:
            op = node.ops[0]

            # Helper to add mutation
            def add_mut(new_op, desc):
                # We need to construct the full list of ops
                new_ops_list = [new_op] + node.ops[1:]
                self.mutations.append(Mutation(node, new_ops_list, node.lineno, node.col_offset, desc, ast.Compare))

            if isinstance(op, ast.Eq):
                add_mut(ast.NotEq(), "Change == to !=")
            elif isinstance(op, ast.NotEq):
                add_mut(ast.Eq(), "Change != to ==")
            elif isinstance(op, ast.Lt):
                add_mut(ast.GtE(), "Change < to >=")
                add_mut(ast.LtE(), "Change < to <=")
            elif isinstance(op, ast.Gt):
                add_mut(ast.LtE(), "Change > to <=")
                add_mut(ast.GtE(), "Change > to >=")
            elif isinstance(op, ast.LtE):
                add_mut(ast.Gt(), "Change <= to >")
                add_mut(ast.Lt(), "Change <= to <")
            elif isinstance(op, ast.GtE):
                add_mut(ast.Lt(), "Change >= to <")
                add_mut(ast.Gt(), "Change >= to >")

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool):
            self.mutations.append(Mutation(node, not node.value, node.lineno, node.col_offset, f"Change {node.value} to {not node.value}", ast.Constant))
        self.generic_visit(node)

class MutationTester:
    def __init__(self, project_dir: Path, target_file: Path, test_command: Optional[List[str]] = None):
        self.project_dir = project_dir.resolve()
        self.target_file = target_file.resolve()
        self.test_command = test_command or self._detect_test_command()

    def _detect_test_command(self) -> List[str]:
        # Prefer pytest if available
        if shutil.which("pytest"):
            return ["pytest"]
        return [sys.executable, "-m", "unittest"]

    def run(self):
        console.print(f"[bold blue]Mutation Testing: {self.target_file}[/bold blue]")
        console.print(f"Test Command: {' '.join(self.test_command)}")

        try:
            original_content = self.target_file.read_text()
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {self.target_file}[/red]")
            return

        try:
            tree = ast.parse(original_content)
        except SyntaxError as e:
            console.print(f"[red]Syntax Error parsing target file: {e}[/red]")
            return

        visitor = MutationVisitor()
        visitor.visit(tree)

        mutations = visitor.mutations
        if not mutations:
            console.print("[yellow]No mutations found.[/yellow]")
            return

        console.print(f"Found {len(mutations)} mutation points.")

        # Baseline run
        console.print("Running baseline tests...")
        if not self._run_tests():
            console.print("[bold red]Baseline tests failed! Fix tests before running mutation testing.[/bold red]")
            return
        console.print("[green]Baseline tests passed.[/green]")

        killed = 0
        errors = 0

        table = Table(title="Mutation Results")
        table.add_column("ID", style="cyan")
        table.add_column("Line", style="magenta")
        table.add_column("Mutation", style="yellow")
        table.add_column("Result", style="bold")

        with console.status("[bold green]Running mutations...[/bold green]") as status:
            for i, mutation in enumerate(mutations):
                mutation_id = str(i + 1)
                status.update(f"[bold green]Running mutation {mutation_id}/{len(mutations)}...[/bold green]")

                # Apply mutation
                modified_tree = self._apply_mutation_to_tree(original_content, mutation)

                if not modified_tree:
                    console.print(f"[red]Failed to apply mutation {mutation_id}[/red]")
                    errors += 1
                    continue

                try:
                    modified_code = ast.unparse(modified_tree)
                except Exception as e:
                    console.print(f"[red]Error unparsing tree for mutation {mutation_id}: {e}[/red]")
                    errors += 1
                    continue

                # Write modified code
                self.target_file.write_text(modified_code)

                try:
                    # Run test
                    passed = self._run_tests()
                    if passed:
                        result = "[red]SURVIVED[/red]"
                    else:
                        result = "[green]KILLED[/green]"
                        killed += 1
                except Exception:
                    result = "[red]ERROR[/red]"
                    errors += 1
                finally:
                    # Restore original
                    self.target_file.write_text(original_content)

                table.add_row(mutation_id, str(mutation.lineno), mutation.description, result)

        console.print(table)

        total = len(mutations)
        score = (killed / total) * 100 if total > 0 else 0.0
        color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
        console.print(f"\n[bold]Mutation Score: [{color}]{score:.2f}%[/{color}][/bold] ({killed}/{total} killed)")

    def _apply_mutation_to_tree(self, original_content: str, mutation: Mutation) -> Optional[ast.AST]:
        fresh_tree = ast.parse(original_content)

        target_node = None
        # We need to find the node again in the fresh tree.
        for node in ast.walk(fresh_tree):
            if (getattr(node, 'lineno', -1) == mutation.lineno and
                getattr(node, 'col_offset', -1) == mutation.col_offset and
                isinstance(node, mutation.node_type)):
                target_node = node
                break

        if target_node:
            if isinstance(target_node, ast.BinOp):
                target_node.op = mutation.mutation_op
            elif isinstance(target_node, ast.Compare):
                target_node.ops = mutation.mutation_op
            elif isinstance(target_node, ast.Constant):
                target_node.value = mutation.mutation_op
            return fresh_tree
        return None

    def _run_tests(self) -> bool:
        """Returns True if tests PASS, False if they FAIL."""
        try:
            # Capture output to avoid spamming console
            # Using timeout to kill infinite loops caused by mutations
            # Ensure we don't use stale bytecode
            env = sys.modules['os'].environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            result = subprocess.run(
                self.test_command,
                cwd=self.project_dir,
                capture_output=True,
                check=False,
                timeout=10, # 10s timeout for single mutation run
                env=env
            )
            if result.returncode != 0:
                # console.print(f"DEBUG: Tests failed with code {result.returncode}")
                # console.print(result.stdout.decode())
                # console.print(result.stderr.decode())
                pass
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            # Timeout counts as killed (mutation caused infinite loop or hang)
            return False
        except Exception as e:
            console.print(f"[red]Error running tests: {e}[/red]")
            return False

def run_mutate(project_dir: Path, target_file: str, test_command: str = None):
    # If target_file is not absolute, resolve it relative to project_dir
    target_path = Path(target_file)
    if not target_path.is_absolute():
        target_path = project_dir / target_path

    tester = MutationTester(
        project_dir=project_dir,
        target_file=target_path,
        test_command=test_command.split() if test_command else None
    )
    tester.run()
