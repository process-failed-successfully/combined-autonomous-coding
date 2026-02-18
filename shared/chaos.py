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
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Callable, Dict, Type
from abc import ABC, abstractmethod

# Configure logger
logger = logging.getLogger(__name__)

class ChaosExperiment(ABC):
    """Abstract base class for chaos experiments."""

    def __init__(self, project_dir: Path, dry_run: bool = False, printer: Callable[[str], None] = print, **kwargs):
        self.project_dir = project_dir
        self.dry_run = dry_run
        self.printer = printer
        self.kwargs = kwargs

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


class KillProcessExperiment(ChaosExperiment):
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
            self.printer(f"Error listing processes: {e}")
            return False

        if not targets:
            self.printer("  No suitable target processes found.")
            return False

        # Pick a victim
        victim = random.choice(targets)
        self.printer(f"  🎯 Target identified: {victim.info['name']} (PID: {victim.info['pid']})")

        if self.dry_run:
            self.printer(f"  [Dry Run] Would kill process {victim.info['pid']}")
            return True

        try:
            self.printer(f"  🔪 Killing process {victim.info['pid']}...")
            victim.terminate()
            victim.wait(timeout=3)
            self.printer("  ✅ Process terminated.")
            return True
        except psutil.NoSuchProcess:
            self.printer("  ⚠️  Process already gone.")
            return False
        except psutil.TimeoutExpired:
            self.printer("  ⚠️  Process did not terminate gracefully. Forcing kill...")
            victim.kill()
            return True
        except Exception as e:
            self.printer(f"  ❌ Error killing process: {e}")
            return False


class FileJitterExperiment(ChaosExperiment):
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
            self.printer("  No source files found.")
            return False

        target_file = random.choice(files)
        self.printer(f"  🎯 Target file: {target_file.relative_to(self.project_dir)}")

        if self.dry_run:
            self.printer(f"  [Dry Run] Would touch {target_file}")
            return True

        try:
            # Just touch the file (update mtime)
            self.printer(f"  👉 Touching file...")
            target_file.touch()
            self.printer("  ✅ File touched.")
            return True
        except Exception as e:
            self.printer(f"  ❌ Error touching file: {e}")
            return False

class NetworkChaosExperiment(ChaosExperiment):
    """Base class for network chaos experiments using tc."""

    def __init__(self, project_dir: Path, dry_run: bool = False, printer: Callable[[str], None] = print, **kwargs):
        super().__init__(project_dir, dry_run, printer, **kwargs)
        self.interface = kwargs.get("interface", "eth0")

    def check_tc(self) -> bool:
        if not shutil.which("tc"):
            self.printer("❌ 'tc' command not found. Please install iproute2.")
            return False
        return True

    def run_tc(self, args: List[str]) -> bool:
        cmd = ["sudo", "tc"] + args
        if self.dry_run:
            self.printer(f"  [Dry Run] Would run: {' '.join(cmd)}")
            return True

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            self.printer(f"  ❌ Error running tc: {e.stderr.strip()}")
            return False

    def cleanup(self):
        """Clears root qdisc."""
        self.printer(f"  🧹 Cleaning up network rules on {self.interface}...")
        # Ignore errors if qdisc doesn't exist
        cmd = ["sudo", "tc", "qdisc", "del", "dev", self.interface, "root"]

        if self.dry_run:
            self.printer(f"  [Dry Run] Would run: {' '.join(cmd)}")
            return

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # "No such file or directory" usually means no qdisc exists, which is fine
            if "No such file or directory" not in e.stderr and "RTNETLINK answers: No such file or directory" not in e.stderr:
                 # Check if exit code is 2 (ENOENT-ish for some tools) or check message
                 self.printer(f"  ℹ️  Cleanup note: {e.stderr.strip()}")

class NetworkLatencyExperiment(NetworkChaosExperiment):
    """Injects network latency."""

    @property
    def name(self) -> str:
        return "network-latency"

    @property
    def description(self) -> str:
        return f"Injects 500ms latency on {self.interface} for 30 seconds."

    def run(self) -> bool:
        if not self.check_tc():
            return False

        self.printer(f"  ⏱️  Injecting 500ms latency (+/- 50ms) on {self.interface}...")

        # Use 'replace' instead of 'add' to handle existing rules, or just cleanup first?
        # 'replace' is safer if rules exist.
        op = "replace"
        # However, replace fails if no qdisc exists on some kernels? No, replace adds if missing.
        # But for root qdisc, 'add' is standard for first time. 'replace' works if one exists.
        # Let's try 'add' but catch "File exists" and try 'change'/'replace'?
        # Or just use 'replace'. `tc qdisc replace ...` is generally supported.

        success = self.run_tc(["qdisc", "replace", "dev", self.interface, "root", "netem", "delay", "500ms", "50ms", "distribution", "normal"])

        if not success:
             # Try adding if replace failed (though replace should cover add)
             # self.printer("  ⚠️  Replace failed, trying add...")
             # success = self.run_tc(["qdisc", "add", "dev", self.interface, "root", "netem", "delay", "500ms", "50ms", "distribution", "normal"])
             return False

        if self.dry_run:
            return True

        try:
            self.printer("  ⏳ Waiting 30 seconds...")
            time.sleep(30)
        except KeyboardInterrupt:
            self.printer("\n  ⚠️  Interrupted!")
        finally:
            self.cleanup()

        self.printer("  ✅ Network latency experiment complete.")
        return True

class NetworkLossExperiment(NetworkChaosExperiment):
    """Injects network packet loss."""

    @property
    def name(self) -> str:
        return "network-loss"

    @property
    def description(self) -> str:
        return f"Injects 10% packet loss on {self.interface} for 30 seconds."

    def run(self) -> bool:
        if not self.check_tc():
            return False

        self.printer(f"  📉 Injecting 10% packet loss on {self.interface}...")
        success = self.run_tc(["qdisc", "replace", "dev", self.interface, "root", "netem", "loss", "10%"])

        if not success:
            return False

        if self.dry_run:
            return True

        try:
            self.printer("  ⏳ Waiting 30 seconds...")
            time.sleep(30)
        except KeyboardInterrupt:
            self.printer("\n  ⚠️  Interrupted!")
        finally:
            self.cleanup()

        self.printer("  ✅ Network loss experiment complete.")
        return True

class NetworkResetExperiment(NetworkChaosExperiment):
    """Resets network rules."""

    @property
    def name(self) -> str:
        return "network-reset"

    @property
    def description(self) -> str:
        return f"Manually resets all network traffic control rules on {self.interface}."

    def run(self) -> bool:
        if not self.check_tc():
            return False

        self.cleanup()
        self.printer("  ✅ Network rules reset.")
        return True


class ChaosManager:
    def __init__(self, project_dir: Path, printer: Callable[[str], None] = print):
        self.project_dir = project_dir
        self.printer = printer
        self.experiments: Dict[str, Type[ChaosExperiment]] = {
            "kill-process": KillProcessExperiment,
            "file-jitter": FileJitterExperiment,
            "network-latency": NetworkLatencyExperiment,
            "network-loss": NetworkLossExperiment,
            "network-reset": NetworkResetExperiment
        }

    def list_experiments(self):
        self.printer("Available Chaos Experiments:")
        for name, cls in self.experiments.items():
            # Instantiate with default args for description
            exp = cls(self.project_dir, printer=self.printer)
            self.printer(f"  - {name}: {exp.description}")

    def run(self, action: str, dry_run: bool = False, yes: bool = False, **kwargs) -> bool:
        if action not in self.experiments:
            self.printer(f"❌ Unknown chaos experiment: {action}")
            return False

        exp_cls = self.experiments[action]
        experiment = exp_cls(self.project_dir, dry_run, printer=self.printer, **kwargs)

        self.printer(f"--- Chaos Experiment: {experiment.name} ---")
        self.printer(f"Description: {experiment.description}")

        if not dry_run and not yes:
            confirm = input("⚠️  Are you sure you want to proceed? This may disrupt your work. [y/N]: ").strip().lower()
            if confirm != 'y':
                self.printer("Aborted.")
                return False

        return experiment.run()


def run_chaos_logic(project_dir: Path, action: str, dry_run: bool = False, yes: bool = False, interface: str = "eth0"):
    """Entry point for the chaos command."""
    manager = ChaosManager(project_dir)

    if action == "list":
        manager.list_experiments()
    else:
        manager.run(action, dry_run, yes, interface=interface)
