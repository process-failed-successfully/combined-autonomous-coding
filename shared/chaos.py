"""
Chaos Engineering for Local Development
=======================================

Provides tools to simulate failures and stress-test the development environment.
"""

import os
import sys
import time
import random
import logging
import psutil
from pathlib import Path
from typing import List, Optional
from abc import ABC, abstractmethod

# Configure logger
logger = logging.getLogger(__name__)

class ChaosExperiment(ABC):
    """Abstract base class for chaos experiments."""

    def __init__(self, project_dir: Path, dry_run: bool = False):
        self.project_dir = project_dir
        self.dry_run = dry_run

    @abstractmethod
    def run(self) -> bool:
        """Executes the experiment. Returns True if successful (chaos injected)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class ProcessKiller(ChaosExperiment):
    """Randomly kills development processes."""

    @property
    def name(self) -> str:
        return "kill-process"

    @property
    def description(self) -> str:
        return "Terminates random development processes (node, python, go) running in the project."

    def run(self) -> bool:
        targets = []
        try:
            # Find processes running from the project directory
            for proc in psutil.process_iter(['pid', 'name', 'cwd', 'cmdline']):
                try:
                    cwd = proc.info.get('cwd')
                    name = proc.info.get('name')

                    if not cwd or not name:
                        continue

                    # Check if process is running within project dir
                    # Normalize paths
                    try:
                        proc_path = Path(cwd).resolve()
                        proj_path = self.project_dir.resolve()
                        if proj_path in proc_path.parents or proj_path == proc_path:
                            # Filter for interesting processes
                            if name in ['node', 'python', 'python3', 'go', 'java', 'npm', 'yarn', 'pnpm']:
                                # Avoid killing the agent itself
                                if proc.pid == os.getpid():
                                    continue
                                targets.append(proc)
                    except (ValueError, OSError):
                        continue

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.error(f"Error listing processes: {e}")
            return False

        if not targets:
            print("  No suitable target processes found.")
            return False

        # Pick a victim
        victim = random.choice(targets)
        print(f"  🎯 Target identified: {victim.info['name']} (PID: {victim.info['pid']})")

        if self.dry_run:
            print(f"  [Dry Run] Would kill process {victim.info['pid']}")
            return True

        try:
            print(f"  🔪 Killing process {victim.info['pid']}...")
            victim.terminate()
            victim.wait(timeout=3)
            print("  ✅ Process terminated.")
            return True
        except psutil.NoSuchProcess:
            print("  ⚠️  Process already gone.")
            return False
        except psutil.TimeoutExpired:
            print("  ⚠️  Process did not terminate gracefully. Forcing kill...")
            victim.kill()
            return True
        except Exception as e:
            print(f"  ❌ Error killing process: {e}")
            return False


class FileJitter(ChaosExperiment):
    """Touches or modifies files to trigger watchers."""

    @property
    def name(self) -> str:
        return "file-jitter"

    @property
    def description(self) -> str:
        return "Touches source files to trigger hot-reloading watchers."

    def run(self) -> bool:
        # Find source files
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.html', '.css'}
        files = []

        for root, dirs, filenames in os.walk(self.project_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            if 'node_modules' in dirs:
                dirs.remove('node_modules')
            if '.venv' in dirs:
                dirs.remove('.venv')

            for f in filenames:
                if Path(f).suffix in extensions:
                    files.append(Path(root) / f)

        if not files:
            print("  No source files found.")
            return False

        target_file = random.choice(files)
        print(f"  🎯 Target file: {target_file.relative_to(self.project_dir)}")

        if self.dry_run:
            print(f"  [Dry Run] Would touch {target_file}")
            return True

        try:
            # Just touch the file (update mtime)
            print(f"  👉 Touching file...")
            target_file.touch()
            print("  ✅ File touched.")
            return True
        except Exception as e:
            print(f"  ❌ Error touching file: {e}")
            return False


class ChaosManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.experiments: dict[str, type[ChaosExperiment]] = {
            "kill-process": ProcessKiller,
            "file-jitter": FileJitter
        }

    def list_experiments(self):
        print("Available Chaos Experiments:")
        for name, cls in self.experiments.items():
            exp = cls(self.project_dir)
            print(f"  - {name}: {exp.description}")

    def run(self, action: str, dry_run: bool = False, yes: bool = False) -> bool:
        if action not in self.experiments:
            print(f"❌ Unknown chaos experiment: {action}")
            return False

        exp_cls = self.experiments[action]
        experiment = exp_cls(self.project_dir, dry_run)

        print(f"--- Chaos Experiment: {experiment.name} ---")
        print(f"Description: {experiment.description}")

        if not dry_run and not yes:
            confirm = input("⚠️  Are you sure you want to proceed? This may disrupt your work. [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                return False

        return experiment.run()


def run_chaos_logic(project_dir: Path, action: str, dry_run: bool = False, yes: bool = False):
    """Entry point for the chaos command."""
    manager = ChaosManager(project_dir)

    if action == "list":
        manager.list_experiments()
    else:
        manager.run(action, dry_run, yes)
