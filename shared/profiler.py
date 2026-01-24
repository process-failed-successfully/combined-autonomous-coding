"""
Profiler Manager
================

Manages performance profiling of scripts using cProfile and provides reporting.
"""

import sys
import pstats
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)

class ProfilerManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.stats_file = self.project_dir / ".perf.stats"
        self.console = Console()

    def run(self, script_path: Path, args: List[str]) -> bool:
        """Runs the script with cProfile and saves stats."""
        # Ensure script path is handled correctly (absolute or relative)
        if not script_path.is_absolute():
            script_full_path = self.project_dir / script_path
        else:
            script_full_path = script_path

        if not script_full_path.exists():
            self.console.print(f"[bold red]Error: Script not found at {script_full_path}[/bold red]")
            return False

        # Construct command: python -m cProfile -o .perf.stats script.py [args]
        cmd = [sys.executable, "-m", "cProfile", "-o", str(self.stats_file), str(script_full_path)] + args

        self.console.print(f"[bold green]Running profiler on {script_full_path.name}...[/bold green]")
        # Mask the full path for cleaner output if inside project
        try:
            display_cmd = f"python -m cProfile -o .perf.stats {script_full_path.relative_to(self.project_dir)} {' '.join(args)}"
        except ValueError:
            display_cmd = f"python -m cProfile -o .perf.stats {script_full_path} {' '.join(args)}"

        self.console.print(f"Command: {display_cmd}")

        try:
            # We want to show output to user, so we don't capture output unless we want to hide it.
            # Allowing stdout/stderr to flow through is usually better for a CLI runner.
            result = subprocess.run(cmd, cwd=self.project_dir)

            if result.returncode != 0:
                self.console.print(f"[bold red]Script failed with exit code {result.returncode}.[/bold red]")
                # We still might have stats?
                if not self.stats_file.exists():
                    return False

            self.console.print(f"[bold green]Profiling complete. Stats saved to {self.stats_file.name}[/bold green]")
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error running profiler: {e}[/bold red]")
            return False

    def report(self, limit: int = 20, sort_by: str = "tottime"):
        """Generates a rich text report from the stats file."""
        if not self.stats_file.exists():
            self.console.print(f"[red]Stats file {self.stats_file.name} not found. Run 'perf run <script>' first.[/red]")
            return

        try:
            p = pstats.Stats(str(self.stats_file))
            # sort_by mapping to pstats keys if needed, but 'tottime', 'cumtime', 'ncalls' are standard
            p.sort_stats(sort_by)

            table = Table(title=f"Performance Profile (Sorted by {sort_by})")
            table.add_column("Calls", justify="right")
            table.add_column("Total Time", justify="right")
            table.add_column("Per Call", justify="right")
            table.add_column("Cum Time", justify="right")
            table.add_column("Function", style="cyan")

            # p.stats is a dict: func -> (cc, nc, tt, ct, callers)
            # func is (filename, line, name)

            count = 0
            # p.fcn_list is populated after sort_stats()
            for func in p.fcn_list:
                if count >= limit:
                    break

                cc, nc, tt, ct, callers = p.stats[func]
                filename, line, name = func

                # Format calls
                calls = str(nc)
                if cc != nc:
                    calls = f"{nc}/{cc}"

                # Per call (tottime per call)
                percall = tt / nc if nc > 0 else 0

                # Formatting filename
                file_path = Path(filename)
                file_display = f"{file_path.name}:{line}"

                # Try to make it relative to project dir
                if str(self.project_dir) in str(file_path):
                    try:
                        file_display = f"{file_path.relative_to(self.project_dir)}:{line}"
                    except ValueError:
                        pass

                # Special handling for built-in/method descriptors which might look like '~' or '<string>'
                if filename == "~":
                    file_display = "(built-in)"
                elif filename.startswith("<") and filename.endswith(">"):
                    file_display = filename

                func_display = f"{name} ({file_display})"

                table.add_row(
                    calls,
                    f"{tt:.4f}",
                    f"{percall:.4f}",
                    f"{ct:.4f}",
                    func_display
                )
                count += 1

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[bold red]Error parsing stats file: {e}[/bold red]")
