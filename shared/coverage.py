"""
Coverage Manager
================

Runs tests with coverage and displays/generates reports.
"""

import subprocess
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Any, List

def check_dependencies() -> bool:
    """Checks if pytest and pytest-cov are installed."""
    if not shutil.which("pytest"):
        return False

    # Check for pytest-cov plugin
    try:
        result = subprocess.run(
            ["pytest", "--help"],
            capture_output=True,
            text=True
        )
        if "--cov" not in result.stdout:
            return False
    except subprocess.CalledProcessError:
        return False

    return True

def parse_coverage_xml(xml_path: Path) -> Dict[str, Any]:
    """Parses coverage.xml to get a summary."""
    if not xml_path.exists():
        return {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Coverage.py XML format
        line_rate = float(root.attrib.get("line-rate", 0))
        branch_rate = float(root.attrib.get("branch-rate", 0))

        # Calculate percentage
        percentage = line_rate * 100

        return {
            "total_coverage": percentage,
            "line_rate": line_rate,
            "branch_rate": branch_rate,
            "packages": len(root.findall(".//package")),
            "classes": len(root.findall(".//class")),
        }
    except Exception as e:
        print(f"Error parsing coverage XML: {e}", file=sys.stderr)
        return {}

def run_coverage_logic(
    project_dir: Path,
    html_report: bool = False,
    xml_report: bool = False,
    fail_under: Optional[int] = None,
    test_args: Optional[List[str]] = None
) -> bool:
    """
    Runs pytest with coverage configuration.

    Args:
        project_dir: The root directory of the project.
        html_report: Whether to generate an HTML report (htmlcov/).
        xml_report: Whether to generate an XML report (coverage.xml).
        fail_under: Percentage threshold to fail the command.
        test_args: Additional arguments for pytest.

    Returns:
        True if tests passed and coverage requirement met, False otherwise.
    """
    if not check_dependencies():
        print("❌ Error: 'pytest' or 'pytest-cov' not found.")
        print("Please run: pip install pytest pytest-cov")
        return False

    project_dir = project_dir.resolve()

    cmd = ["pytest", f"--cov={project_dir}", "--cov-report=term-missing"]

    if html_report:
        cmd.append("--cov-report=html")

    if xml_report:
        cmd.append("--cov-report=xml")

    if fail_under is not None:
        cmd.append(f"--cov-fail-under={fail_under}")

    if test_args:
        cmd.extend(test_args)
    else:
        # Default to finding tests in the project dir
        cmd.append(str(project_dir))

    print(f"--- Running Coverage: {' '.join(cmd)} ---")

    try:
        # We stream output to the console so the user sees progress
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            text=True
        )

        if result.returncode == 0:
            print("\n✅ Tests passed and coverage thresholds met.")

            # Post-run analysis if XML was generated (or force generated temporarily?)
            # Actually, standard output usually gives a good summary.
            # If the user asked for XML, we can parse it to give a nicer summary if we wanted,
            # but pytest-cov's term-missing report is usually sufficient.

            if html_report:
                html_path = project_dir / "htmlcov" / "index.html"
                print(f"📊 HTML Report generated: {html_path}")

            if xml_report:
                xml_path = project_dir / "coverage.xml"
                print(f"📊 XML Report generated: {xml_path}")

            return True
        else:
            print("\n❌ Tests failed or coverage threshold not met.")
            return False

    except KeyboardInterrupt:
        print("\nAborted.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
