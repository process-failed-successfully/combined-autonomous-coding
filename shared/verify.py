import sys
import subprocess  # nosec
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

def run_command(command: List[str], cwd: Path, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Runs a shell command and returns the result."""
    try:
        return subprocess.run(  # nosec
            command,
            cwd=str(cwd),
            capture_output=capture_output,
            text=True,
            check=False  # We handle return codes manually
        )
    except Exception as e:
        # Create a dummy CompletedProcess to represent the failure
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout="",
            stderr=str(e)
        )

def check_dependencies() -> List[str]:
    """Checks if required tools are installed."""
    missing = []
    for tool in ["flake8", "mypy", "bandit", "pytest"]:
        if not shutil.which(tool):
            missing.append(tool)
    return missing

def run_formatter(project_dir: Path, output_format: str = "text") -> Dict[str, Any]:
    """Runs a code formatter (black or autopep8)."""
    if shutil.which("black"):
        print("Running Formatter (Black)...")
        cmd = ["black", "."]
    elif shutil.which("autopep8"):
        print("Running Formatter (Autopep8)...")
        cmd = ["autopep8", "--in-place", "--recursive", "."]
    else:
        return {
            "check": "format",
            "success": False,
            "stdout": "",
            "stderr": "No formatter found (black or autopep8)."
        }

    result = run_command(cmd, project_dir)
    success = result.returncode == 0
    return {
        "check": "format",
        "success": success,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def run_lint(project_dir: Path, output_format: str = "text") -> Dict[str, Any]:
    """Runs flake8 linting."""
    print("Running Lint (Flake8)...")
    cmd = ["flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics", "--exclude=.venv,venv,build,dist"]

    result = run_command(cmd, project_dir)

    # Second pass for warnings (non-blocking in script but we capture it)
    cmd_warnings = ["flake8", ".", "--count", "--exit-zero", "--max-complexity=35", "--max-line-length=160", "--statistics", "--exclude=.venv,venv,build,dist"]
    result_warnings = run_command(cmd_warnings, project_dir)

    success = result.returncode == 0
    return {
        "check": "lint",
        "success": success,
        "stdout": result.stdout + "\n" + result_warnings.stdout,
        "stderr": result.stderr
    }

def run_type_check(project_dir: Path, output_format: str = "text") -> Dict[str, Any]:
    """Runs mypy type checking."""
    print("Running Type Check (Mypy)...")
    cmd = ["mypy", ".", "--ignore-missing-imports", "--no-strict-optional"]
    result = run_command(cmd, project_dir)

    # Mypy returns 0 on success, non-zero on issues
    success = result.returncode == 0
    return {
        "check": "type_check",
        "success": success,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def run_security_scan(project_dir: Path, output_format: str = "text") -> Dict[str, Any]:
    """Runs bandit security scan."""
    print("Running Security Scan (Bandit)...")
    # Using baseline if it exists
    cmd = ["bandit", "-r", ".", "-ll", "-x", ".venv,venv,build,tests"]

    if (project_dir / "pyproject.toml").exists():
        cmd.extend(["-c", "pyproject.toml"])

    if (project_dir / "bandit_baseline.json").exists():
        cmd.extend(["-b", "bandit_baseline.json", "-f", "custom"])

    result = run_command(cmd, project_dir)

    success = result.returncode == 0
    return {
        "check": "security",
        "success": success,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def run_tests(project_dir: Path, output_format: str = "text") -> Dict[str, Any]:
    """Runs pytest."""
    print("Running Tests (Pytest)...")
    cmd = ["pytest", "--cov=.", "--cov-report=term-missing", "tests/"]

    # Adjust python path to include project dir
    env = None # Inherit env by default

    if shutil.which("pytest"):
        # We can run directly
        pass
    else:
        # Try running as module
        cmd = [sys.executable, "-m", "pytest", "--cov=.", "--cov-report=term-missing", "tests/"]

    # We need to set PYTHONPATH to include the current directory
    # subprocess.run handles env inheritance, but we need to modify PYTHONPATH
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}:{project_dir.resolve()}"

    try:
        result = subprocess.run(  # nosec
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            check=False,
            env=env
        )
    except Exception as e:
        return {
            "check": "test",
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

    success = result.returncode == 0
    return {
        "check": "test",
        "success": success,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def run_verify_logic(
    project_dir: Path,
    checks: List[str] = None,
    fix: bool = False,
    output_format: str = "text"
) -> bool:
    """
    Runs the verification checks.

    Args:
        project_dir: The project directory.
        checks: List of checks to run ['lint', 'type', 'security', 'test']. None means all.
        fix: Whether to attempt auto-fixes.
        output_format: 'text' or 'json'.

    Returns:
        True if all selected checks pass, False otherwise.
    """
    if not checks or "all" in checks:
        checks = ["lint", "type", "security", "test"]

    project_dir = project_dir.resolve()
    results = []

    missing_deps = check_dependencies()
    if missing_deps:
        msg = f"Missing dependencies: {', '.join(missing_deps)}. Please run 'pip install -r requirements-dev.txt'."
        if output_format == "json":
            print(json.dumps({"error": msg}))
        else:
            print(f"❌ {msg}")
        return False

    if fix:
        format_result = run_formatter(project_dir, output_format)
        results.append(format_result)
        # If formatter fails (e.g. not found), we might want to warn but continue
        if not format_result["success"] and format_result["stderr"]:
             # Just append to output, will be shown in summary
             pass

    if "lint" in checks:
        results.append(run_lint(project_dir, output_format))

    if "type" in checks:
        results.append(run_type_check(project_dir, output_format))

    if "security" in checks:
        results.append(run_security_scan(project_dir, output_format))

    if "test" in checks:
        results.append(run_tests(project_dir, output_format))

    # Output generation
    if output_format == "json":
        print(json.dumps(results, indent=2))
        return all(r["success"] for r in results)

    # Text Output
    print("\n========================================")
    print("  VERIFICATION SUMMARY")
    print("========================================")

    all_passed = True
    for res in results:
        check_name = res["check"].upper()
        status = "✅ PASS" if res["success"] else "❌ FAIL"
        if not res["success"]:
            all_passed = False

        print(f"[{status}] {check_name}")

        if not res["success"] or (res["stdout"] and check_name != "TEST"): # Always show output on fail, or if there is output
             # Indent output
             print("-" * 20)
             if res["stdout"].strip():
                 print(res["stdout"].strip())
             if res["stderr"].strip():
                 print(res["stderr"].strip())
             print("-" * 20)
             print()

    if all_passed:
        print("\n\033[0;32mAll Checks Passed Successfully!\033[0m")
    else:
        print("\n\033[0;31mSome checks failed. Please review the output above.\033[0m")

    return all_passed
