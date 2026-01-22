import subprocess
import time
import statistics
import shlex
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

@dataclass
class BenchmarkResult:
    command: str
    mean: float
    median: float
    stddev: float
    min: float
    max: float
    runs: List[float]

class BenchmarkRunner:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def run(self, commands: List[str], iterations: int = 10, warmup: int = 0) -> List[BenchmarkResult]:
        results = []

        for cmd in commands:
            times = []

            # Warmup
            if warmup > 0:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[bold yellow]Warming up: {cmd}"),
                    transient=True,
                    console=self.console
                ) as progress:
                    task = progress.add_task("Warmup", total=warmup)
                    for _ in range(warmup):
                        self._execute(cmd)
                        progress.advance(task)

            # Benchmark
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[bold green]Benchmarking: {cmd}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Running", total=iterations)

                for _ in range(iterations):
                    start_time = time.perf_counter()
                    self._execute(cmd)
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                    progress.advance(task)

            if not times:
                continue

            mean_val = statistics.mean(times)
            median_val = statistics.median(times)
            min_val = min(times)
            max_val = max(times)
            stddev_val = statistics.stdev(times) if len(times) > 1 else 0.0

            results.append(BenchmarkResult(
                command=cmd,
                mean=mean_val,
                median=median_val,
                stddev=stddev_val,
                min=min_val,
                max=max_val,
                runs=times
            ))

        return results

    def _execute(self, command: str):
        # Using shell=True to support complex commands with pipes/redirects
        # Using executable='/bin/bash' (or equivalent) might be safer but shell=True is standard for bench tools
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    def print_report(self, results: List[BenchmarkResult]):
        if not results:
            self.console.print("No results to display.")
            return

        # Sort by mean time (fastest first)
        results.sort(key=lambda x: x.mean)
        fastest = results[0]

        table = Table(title="Benchmark Results")
        table.add_column("Command", style="cyan")
        table.add_column("Mean", justify="right", style="green")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
        table.add_column("Relative", justify="right", style="bold magenta")

        for res in results:
            mean_str = f"{res.mean:.4f} s"
            min_str = f"{res.min:.4f} s"
            max_str = f"{res.max:.4f} s"

            if res == fastest:
                relative = "1.00"
            else:
                ratio = res.mean / fastest.mean
                relative = f"{ratio:.2f}x slower"

            table.add_row(res.command, mean_str, min_str, max_str, relative)

        self.console.print(table)

def run_measure_logic(commands: List[str], iterations: int = 10, warmup: int = 0):
    runner = BenchmarkRunner()
    results = runner.run(commands, iterations, warmup)
    runner.print_report(results)
    return True
