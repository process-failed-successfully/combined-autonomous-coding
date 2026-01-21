"""
Code Polish Manager
===================

Proactively identifies and refactors code quality issues using AI.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table

from shared.complexity import analyze_project_complexity
from shared.refactor import RefactorManager

class PolishManager:
    def __init__(self, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
        self.project_dir = project_dir
        self.refactor_manager = RefactorManager(project_dir)
        self.agent_type = agent_type
        self.model = model
        self.console = Console()

    def scan_complexity(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Scans for functions with high cyclomatic complexity."""
        self.console.print("[bold]Scanning for complexity hotspots...[/bold]")
        results = analyze_project_complexity(self.project_dir)

        # Filter by threshold
        hotspots = [r for r in results if r["complexity"] > threshold]

        # Sort by complexity descending
        hotspots.sort(key=lambda x: x["complexity"], reverse=True)
        return hotspots

    async def polish_hotspot(self, hotspot: Dict[str, Any], auto_apply: bool = False, confirm: bool = True) -> bool:
        """
        Refactors a specific hotspot.

        Args:
            hotspot: Dictionary containing 'file', 'function', 'complexity'.
            auto_apply: If True, applies changes without showing diff (use with caution).
            confirm: If True, asks for confirmation before applying.
        """
        file_path = self.project_dir / hotspot["file"]
        function_name = hotspot["function"]
        complexity = hotspot["complexity"]

        self.console.print(f"\n[bold cyan]Polishing:[/bold cyan] {function_name} in {hotspot['file']}")
        self.console.print(f"Current Complexity: [red]{complexity}[/red]")

        instruction = (
            f"Refactor the function `{function_name}` in `{hotspot['file']}` to reduce its "
            f"Cyclomatic Complexity significantly (aim for < 10). "
            f"Break it down into smaller helper functions if necessary. "
            f"Maintain the exact same behavior and public interface."
        )

        try:
            result = await self.refactor_manager.refactor_file(
                target_file=file_path,
                instruction=instruction,
                agent_type=self.agent_type,
                model=self.model
            )
        except Exception as e:
            self.console.print(f"[bold red]Error during refactoring:[/bold red] {e}")
            return False

        if not result["changed"]:
            self.console.print("[yellow]Agent could not find a way to improve the code.[/yellow]")
            return False

        # Show Diff
        self.console.print("\n[bold]Proposed Changes:[/bold]")
        print(result["diff"]) # Using print for diff to keep formatting simple or use a syntax highlighter if available

        if auto_apply:
            self.refactor_manager.apply_changes(file_path, result["new_content"])
            self.console.print(f"[bold green]✅ Applied changes to {file_path.name}[/bold green]")
            return True

        if confirm:
            import sys
            # Simple input fallback if console.input is elusive or we want standard stdin
            response = input("\nApply these changes? [y/N]: ").strip().lower()
            if response == 'y':
                self.refactor_manager.apply_changes(file_path, result["new_content"])
                self.console.print(f"[bold green]✅ Applied changes to {file_path.name}[/bold green]")
                return True
            else:
                self.console.print("[yellow]Skipped.[/yellow]")
                return False

        return False

async def run_polish_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    threshold: int = 10,
    limit: int = 1,
    yes: bool = False
) -> bool:
    """
    Main logic for the polish command.
    """
    manager = PolishManager(project_dir, agent_type, model)

    # 1. Scan
    hotspots = manager.scan_complexity(threshold)

    if not hotspots:
        manager.console.print(f"[green]✅ No functions found with complexity > {threshold}.[/green]")
        return True

    manager.console.print(f"Found {len(hotspots)} hotspot(s).")

    # Display table
    table = Table(title="Complexity Hotspots")
    table.add_column("Complexity", style="red")
    table.add_column("Function", style="cyan")
    table.add_column("File", style="white")

    for h in hotspots[:5]: # Show top 5
        table.add_row(str(h["complexity"]), h["function"], h["file"])

    manager.console.print(table)

    # 2. Iterate and Polish
    count = 0
    for hotspot in hotspots:
        if count >= limit:
            break

        # If not 'yes' (auto-approve interaction), verify user wants to proceed with this specific one
        if not yes:
            response = input(f"\nRefactor `{hotspot['function']}` (Complexity: {hotspot['complexity']})? [Y/n/q]: ").strip().lower()
            if response == 'q':
                break
            if response in ['n', 'no']:
                continue

        # Perform polish
        # If 'yes' flag is passed to command, we still want to show diff but maybe default to apply?
        # Actually standard CLI 'yes' usually means "non-interactive, just do it".
        # But for code refactoring, "just do it" is dangerous.
        # Let's interpret 'yes' as "Skip the 'Do you want to refactor X?' prompt", but still ask for Diff confirmation
        # UNLESS we add a --apply flag.

        # If yes is True, we proceed to polish with auto_apply=True and confirm=False.
        # If yes is False, we prompt for selection (above), and then prompt for diff confirmation (inside polish_hotspot).

        success = await manager.polish_hotspot(hotspot, auto_apply=yes, confirm=not yes)
        if success:
            count += 1

    manager.console.print(f"\n[bold]Polished {count} function(s).[/bold]")
    return True
