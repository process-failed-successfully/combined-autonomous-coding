import subprocess
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any
from shared.dependencies import DependencyAnalyzer, DependencyUpdater


class SecurityRemediator:
    """
    Automates the remediation of security findings (specifically dependency updates).
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.analyzer = DependencyAnalyzer(self.project_dir)
        self.updater = DependencyUpdater(self.project_dir)

    def run_remediation(self, findings: List[Dict[str, Any]], dry_run: bool = False, yes: bool = False) -> Dict[str, Any]:
        """
        Attempts to fix vulnerabilities found in the project.
        """
        results = {
            "fixed": [],
            "failed": [],
            "skipped": []
        }

        # Filter for dependency vulnerabilities
        dep_findings = [f for f in findings if f.get("type") == "dependency"]

        if not dep_findings:
            print("No dependency vulnerabilities to remediate.")
            return results

        print(f"Found {len(dep_findings)} dependency vulnerabilities.")

        # Group by package to avoid duplicate work
        packages_to_fix = {}
        for f in dep_findings:
            # Parse package name from description or snippet
            # Snippet format from SecurityAuditor: "Upgrade {pkg_name}"
            snippet = f.get("snippet", "")
            pkg_name = None
            if snippet.startswith("Upgrade "):
                pkg_name = snippet[8:].strip()
            elif f.get("tool") == "npm audit" and "Vulnerability in " in f.get("description", ""):
                pkg_name = f.get("description", "").replace("Vulnerability in ", "").strip()

            if pkg_name:
                packages_to_fix[pkg_name] = f
            else:
                print(f"Could not parse package name from finding: {f.get('description')}")

        if not packages_to_fix:
            return results

        print(f"Identified {len(packages_to_fix)} unique packages to upgrade.")

        for pkg_name, finding in packages_to_fix.items():
            print(f"\n--- Remediation: {pkg_name} ---")

            # Determine ecosystem
            ecosystem = "unknown"
            if "requirements.txt" in finding.get("file", "") or "pyproject.toml" in finding.get("file", "") or finding.get("tool") == "OSV (PyPI)":
                ecosystem = "python"
            elif "package.json" in finding.get("file", "") or finding.get("tool") == "npm audit":
                ecosystem = "node"

            if ecosystem == "unknown":
                print(f"Skipping {pkg_name}: Unknown ecosystem.")
                results["skipped"].append(pkg_name)
                continue

            # Determine latest version
            latest_version = None
            if ecosystem == "python":
                latest_version = self.analyzer.get_latest_pypi_version(pkg_name)
            elif ecosystem == "node":
                latest_version = self.analyzer.get_latest_npm_version(pkg_name)

            if not latest_version:
                print(f"Skipping {pkg_name}: Could not determine latest version.")
                results["skipped"].append(pkg_name)
                continue

            print(f"Target version: {latest_version}")

            if dry_run:
                print(f"[Dry Run] Would update {pkg_name} to {latest_version} and run tests.")
                results["fixed"].append(pkg_name)  # Count as fixed for dry run reporting
                continue

            if not yes:
                confirm = input(f"Attempt to upgrade {pkg_name} to {latest_version}? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("Skipping.")
                    results["skipped"].append(pkg_name)
                    continue

            # 1. Snapshot file state (simple read)
            # We assume single file for simplicity, but python deps might be in multiple.
            # DependencyUpdater handles locating the file if we pass the right one.
            # SecurityAuditor returns comma-separated files if multiple.
            files = finding.get("file", "").split(", ")
            file_to_update = None

            # Pick the manifest file
            for f in files:
                if f in ["requirements.txt", "package.json", "pyproject.toml"]:
                    file_to_update = self.project_dir / f
                    break

            if not file_to_update or not file_to_update.exists():
                # Fallback based on ecosystem
                if ecosystem == "python":
                    file_to_update = self.project_dir / "requirements.txt"
                elif ecosystem == "node":
                    file_to_update = self.project_dir / "package.json"

            if not file_to_update.exists():
                print(f"Skipping {pkg_name}: Manifest file not found.")
                results["failed"].append(pkg_name)
                continue

            original_content = file_to_update.read_text()

            # 2. Apply Update
            print(f"Updating {pkg_name} in {file_to_update.name}...")
            success = self.updater.update_dependency(file_to_update, pkg_name, latest_version)

            if not success:
                print(f"Failed to update {pkg_name}.")
                results["failed"].append(pkg_name)
                continue

            # 3. Run Tests
            print("Running tests to verify fix...")
            tests_passed = self._run_tests(ecosystem)

            if tests_passed:
                print(f"✅ Tests passed! {pkg_name} upgraded successfully.")
                results["fixed"].append(pkg_name)
            else:
                print(f"❌ Tests failed. Reverting changes for {pkg_name}...")
                file_to_update.write_text(original_content)
                print("Reverted.")
                results["failed"].append(pkg_name)

        return results

    def _run_tests(self, ecosystem: str) -> bool:
        """
        Runs project tests. Returns True if pass, False if fail.
        """
        cmd = []
        if ecosystem == "python":
            # Try pytest
            if shutil.which("pytest"):
                cmd = ["pytest"]
            else:
                cmd = [sys.executable, "-m", "unittest", "discover"]
        elif ecosystem == "node":
            if shutil.which("npm"):
                cmd = ["npm", "test"]
            elif shutil.which("yarn"):
                cmd = ["yarn", "test"]

        if not cmd:
            print("No test runner found.")
            return False  # Conservative: if we can't test, we don't apply the fix automatically?
            # Or maybe we assume it's risky. Let's return False to be safe.

        try:
            # Run with timeout to avoid hanging
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                # Print stderr for debugging
                # print(result.stderr)
                return False
            return True
        except subprocess.TimeoutExpired:
            print("Tests timed out.")
            return False
        except Exception as e:
            print(f"Error running tests: {e}")
            return False
