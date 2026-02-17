import sys
import os
import random
import string
import subprocess
import time
import importlib.util
import inspect
import typing
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

class InputGenerator:
    """Generates random inputs based on type hints."""

    def generate(self, type_hint: Any) -> Any:
        if type_hint == int:
            return self._gen_int()
        elif type_hint == str:
            return self._gen_str()
        elif type_hint == float:
            return self._gen_float()
        elif type_hint == bool:
            return random.choice([True, False])
        elif type_hint == list or getattr(type_hint, "__origin__", None) == list:
            return self._gen_list(type_hint)
        elif type_hint == dict or getattr(type_hint, "__origin__", None) == dict:
            return self._gen_dict(type_hint)
        elif type_hint == typing.Optional or getattr(type_hint, "__origin__", None) == typing.Union:
             # Handle Optional/Union - simplified to try one of the options
             args = getattr(type_hint, "__args__", [])
             if args:
                 return self.generate(random.choice(args))

        # Fallback for unknown or complex types
        return None

    def _gen_int(self):
        # Mix of edge cases and random numbers
        return random.choice([0, 1, -1, 2**32, -2**32, random.randint(-1000, 1000)])

    def _gen_float(self):
        return random.choice([0.0, 1.0, -1.0, float('inf'), float('nan'), random.uniform(-1000.0, 1000.0)])

    def _gen_str(self):
        # Mix of empty, simple, long, and special chars
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        length = random.choice([0, 5, 20, 100, 1000])
        chars = string.ascii_letters + string.digits + special
        return "".join(random.choices(chars, k=length))

    def _gen_list(self, type_hint):
        args = getattr(type_hint, "__args__", [])
        item_type = args[0] if args else int # Default to int list if unknown
        length = random.randint(0, 10)
        return [self.generate(item_type) for _ in range(length)]

    def _gen_dict(self, type_hint):
        # Basic support for Dict[K, V]
        args = getattr(type_hint, "__args__", [])
        key_type = args[0] if args else str
        val_type = args[1] if len(args) > 1 else int
        length = random.randint(0, 5)
        return {self.generate(key_type): self.generate(val_type) for _ in range(length)}


class FuzzLabManager:
    """Manages the fuzzing process."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.generator = InputGenerator()

    def fuzz_cli(self, command: str, count: int = 100, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Fuzzes a CLI command by running it multiple times with random stdin/args.
        NOTE: Currently simple stdin fuzzing.
        """
        crashes = []

        # Split command to get the executable
        parts = command.split()
        if not parts:
            return []

        print(f"Fuzzing CLI command: '{command}' ({count} iterations)...")

        iterator = range(count)
        if HAS_RICH:
            iterator = track(range(count), description="Fuzzing...")

        for i in iterator:
            # Generate random stdin
            fuzz_input = self.generator._gen_str()

            try:
                # We assume the command reads from stdin.
                # Future: Support fuzzing args by injecting into 'parts'

                result = subprocess.run(
                    parts,
                    input=fuzz_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.project_dir
                )

                # Check for crash (non-zero exit code usually, but specifically signals)
                # A segfault return code is usually negative (e.g. -11 for SIGSEGV)
                # In python subprocess, returncode is negative signal number.
                # However, regular errors (exit 1) might not be "crashes" in the fuzzer sense unless strictly defined.
                # Let's consider any non-zero as a potential issue, but highlight signals.

                if result.returncode != 0:
                    # Capture it
                    crash_info = {
                        "iteration": i + 1,
                        "input_preview": fuzz_input[:50],
                        "return_code": result.returncode,
                        "stderr": result.stderr[:200], # Truncate
                        "type": "Crash" if result.returncode < 0 else "Error"
                    }
                    crashes.append(crash_info)

            except subprocess.TimeoutExpired:
                crashes.append({
                    "iteration": i + 1,
                    "input_preview": fuzz_input[:50],
                    "return_code": "TIMEOUT",
                    "stderr": "",
                    "type": "Timeout"
                })
            except Exception as e:
                crashes.append({
                    "iteration": i + 1,
                    "input_preview": fuzz_input[:50],
                    "return_code": "EXCEPTION",
                    "stderr": str(e),
                    "type": "Execution Error"
                })

        return crashes

    def fuzz_function(self, file_path: str, func_name: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        Fuzzes a Python function by importing it and calling with random args.
        """
        # Load module
        path = Path(file_path).resolve()
        if not path.exists():
            print(f"Error: File {path} not found.")
            return []

        module_name = path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(path.parent)) # Add to path to resolve relative imports
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Error importing module: {e}")
            return []
        finally:
            if str(path.parent) in sys.path:
                sys.path.remove(str(path.parent))

        target_func = getattr(module, func_name, None)
        if not target_func:
            print(f"Error: Function '{func_name}' not found in {module_name}.")
            return []

        # Inspect signature
        sig = inspect.signature(target_func)
        params = sig.parameters

        print(f"Fuzzing function '{func_name}' in {path.name} ({count} iterations)...")
        print(f"Signature: {sig}")

        failures = []

        iterator = range(count)
        if HAS_RICH:
            iterator = track(range(count), description="Fuzzing...")

        for i in iterator:
            # Generate args
            args = []
            kwargs = {}

            try:
                for name, param in params.items():
                    if param.annotation == inspect.Parameter.empty:
                        # Default to int if no hint
                        val = self.generator._gen_int()
                    else:
                        val = self.generator.generate(param.annotation)

                    if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                        args.append(val)
                    elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                        kwargs[name] = val
                    # Ignoring VAR_POSITIONAL (*args) and VAR_KEYWORD (**kwargs) for simplicity now

                # Execute
                target_func(*args, **kwargs)

            except Exception as e:
                # We caught an exception!
                failures.append({
                    "iteration": i + 1,
                    "args": [str(a)[:50] for a in args],
                    "kwargs": {k: str(v)[:50] for k,v in kwargs.items()},
                    "error": str(e),
                    "type": type(e).__name__
                })

        return failures


def run_fuzz_lab_logic(args):
    """CLI entry point."""
    manager = FuzzLabManager(args.project_dir)

    if args.action == "cli":
        if not args.target:
            print("Error: --target (command) required for CLI fuzzing.")
            sys.exit(1)

        crashes = manager.fuzz_cli(args.target, count=args.count, timeout=args.timeout)

        if not crashes:
            print("\n✅ Fuzzing complete. No crashes detected.")
            sys.exit(0)

        print(f"\n❌ Found {len(crashes)} issues:")
        if HAS_RICH:
            table = Table(title="CLI Fuzzing Results")
            table.add_column("Iter", style="cyan")
            table.add_column("Type", style="red")
            table.add_column("Input (Preview)", style="white")
            table.add_column("Error/Code", style="yellow")

            for c in crashes[:20]: # Limit output
                table.add_row(str(c['iteration']), c['type'], c['input_preview'].replace("\n", "\\n"), str(c['return_code']))
            console.print(table)
            if len(crashes) > 20:
                print(f"... and {len(crashes) - 20} more.")
        else:
            for c in crashes[:10]:
                print(f"[{c['iteration']}] {c['type']}: Code {c['return_code']} | Input: {c['input_preview']}")

        sys.exit(1)

    elif args.action == "function" or args.action == "func":
        if not args.target:
            print("Error: --target required (format: file.py:function_name).")
            sys.exit(1)

        if ":" not in args.target:
            print("Error: Target must be in format file.py:function_name")
            sys.exit(1)

        file_path, func_name = args.target.split(":", 1)

        failures = manager.fuzz_function(file_path, func_name, count=args.count)

        if not failures:
            print("\n✅ Fuzzing complete. No unhandled exceptions detected.")
            sys.exit(0)

        print(f"\n❌ Found {len(failures)} exceptions:")
        if HAS_RICH:
            table = Table(title="Function Fuzzing Results")
            table.add_column("Iter", style="cyan")
            table.add_column("Type", style="red")
            table.add_column("Args", style="white")
            table.add_column("Error Message", style="yellow")

            for f in failures[:20]:
                args_str = f"{f['args']}, {f['kwargs']}"
                table.add_row(str(f['iteration']), f['type'], args_str[:50], f['error'][:80])
            console.print(table)
        else:
            for f in failures[:10]:
                print(f"[{f['iteration']}] {f['type']}: {f['error']} | Args: {f['args']}")

        sys.exit(1)

    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
