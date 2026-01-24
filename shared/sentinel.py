import time
import sys
import logging
from pathlib import Path
from typing import List, Optional
import asyncio

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object

from shared.verify import run_lint, run_tests, run_type_check, run_security_scan
from shared.troubleshoot import TroubleshootManager

logger = logging.getLogger(__name__)

class SentinelEventHandler(FileSystemEventHandler):
    def __init__(self, project_dir: Path, callback, debounce_seconds: float = 1.0):
        self.project_dir = project_dir
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.last_trigger = 0.0
        self.loop = asyncio.new_event_loop() # Create a dedicated loop for async tasks

    def on_modified(self, event):
        if event.is_directory:
            return

        # Simple ignore patterns (can be improved)
        path = str(event.src_path)
        if any(x in path for x in [".git", "__pycache__", ".venv", "venv", ".agent_", ".perf.stats"]):
            return

        current_time = time.time()
        if current_time - self.last_trigger > self.debounce_seconds:
            self.last_trigger = current_time
            print(f"\n[Sentinel] File modified: {event.src_path}")
            # We need to run the callback in an async context if it's async
            if asyncio.iscoroutinefunction(self.callback):
                self.loop.run_until_complete(self.callback())
            else:
                self.callback()

class Sentinel:
    def __init__(self, project_dir: Path, checks: List[str] = None, auto_fix: bool = False, agent_type: str = "gemini", model: str = None):
        self.project_dir = project_dir
        self.checks = checks or ["lint", "test"]
        self.auto_fix = auto_fix
        self.agent_type = agent_type
        self.model = model
        self.troubleshooter = None

        if self.auto_fix:
            self.troubleshooter = TroubleshootManager(project_dir, agent_type=agent_type, model=model)

    def start(self):
        if Observer is None:
            print("❌ Error: 'watchdog' library not found. Please install it with 'pip install watchdog'.")
            return

        print(f"--- Sentinel Active in {self.project_dir} ---")
        print(f"Checks: {', '.join(self.checks)}")
        print(f"Auto-Fix: {'Enabled' if self.auto_fix else 'Disabled'}")
        if self.auto_fix:
            print(f"Agent: {self.agent_type}")

        event_handler = SentinelEventHandler(self.project_dir, self.run_cycle)
        observer = Observer()
        observer.schedule(event_handler, str(self.project_dir), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n[Sentinel] Stopped.")
        observer.join()

    async def run_cycle(self):
        print(f"[Sentinel] Running checks: {', '.join(self.checks)}...")

        issues = {}

        # 1. Run Checks
        if "lint" in self.checks:
            res = run_lint(self.project_dir)
            if not res["success"]:
                print("❌ Lint Failed")
                issues["lint"] = res
            else:
                print("✅ Lint Passed")

        if "type" in self.checks:
            res = run_type_check(self.project_dir)
            if not res["success"]:
                print("❌ Type Check Failed")
                issues["type"] = res
            else:
                print("✅ Type Check Passed")

        if "security" in self.checks:
            res = run_security_scan(self.project_dir)
            if not res["success"]:
                print("❌ Security Scan Failed")
                issues["security"] = res
            else:
                print("✅ Security Scan Passed")

        if "test" in self.checks:
            res = run_tests(self.project_dir)
            if not res["success"]:
                print("❌ Tests Failed")
                issues["test"] = res
            else:
                print("✅ Tests Passed")

        # 2. Handle Issues
        if not issues:
            print("\n✨ All checks passed. Standing by.")
            return

        if not self.auto_fix:
            print(f"\n⚠️  Found {len(issues)} issues. Auto-fix is disabled.")
            return

        print(f"\n🔧 Auto-Fixing {len(issues)} issues with {self.agent_type}...")

        # Diagnose
        try:
            diagnosis = await self.troubleshooter.diagnose(issues)
            print("\n[Sentinel] Diagnosis:")
            print(diagnosis)

            # Apply
            print("\n[Sentinel] Applying Fix...")
            result = await self.troubleshooter.apply_fix()
            print(result)

            # Verify (Simple re-run message)
            print("\n[Sentinel] Fix applied. Waiting for next change cycle or manual re-trigger.")
            # Optionally we could recurse/re-run immediately, but that risks infinite loops.
            # Ideally, the fix modifies a file, which triggers the watcher again!
            # So we rely on the file system event to verify the fix.

        except Exception as e:
            print(f"❌ Error during auto-fix: {e}")
