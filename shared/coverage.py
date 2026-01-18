"""
Coverage Analysis Utilities
===========================

Functions for running tests with coverage and displaying reports.
"""

import sys
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import namedtuple

CoverageStats = namedtuple("CoverageStats", ["file", "statements", "missed", "percent"])

def get_coverage_color(percent: float) -> str:
    """Returns ANSI color code based on coverage percentage."""
    if percent >= 80:
        return "\033[92m"  # Green
    elif percent >= 50:
        return "\033[93m"  # Yellow
    else:
        return "\033[91m"  # Red

def parse_coverage_xml(xml_path: Path) -> list[CoverageStats]:
    """Parses a coverage.xml file (Cobertura format)."""
    if not xml_path.exists():
        return []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        stats = []

        # Find the source path to make file paths relative if needed
        sources = root.find("sources")
        source_root = Path(sources.find("source").text) if sources is not None and sources.find("source") is not None else Path(".")

        for package in root.findall(".//package"):
            for class_el in package.findall(".//class"):
                filename = class_el.get("filename")

                # Calculate line stats
                lines = class_el.find("lines")
                if lines is None:
                    continue

                total_lines = 0
                missed_lines = 0

                for line in lines.findall("line"):
                    total_lines += 1
                    if int(line.get("hits", 0)) == 0:
                        missed_lines += 1

                if total_lines > 0:
                    percent = ((total_lines - missed_lines) / total_lines) * 100
                else:
                    percent = 100.0

                stats.append(CoverageStats(filename, total_lines, missed_lines, percent))

        return stats
    except ET.ParseError:
        return []

def run_tests_with_coverage(project_dir: Path) -> Path | None:
    """Runs tests with coverage and returns the path to the coverage report."""
    project_dir = project_dir.resolve()

    # 1. Python (pytest)
    if (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        print("Detected Python project. Running pytest with coverage...")

        if not shutil.which("pytest"):
            print("❌ Error: 'pytest' not found. Please install it with 'pip install pytest pytest-cov'.")
            return None

        xml_report = project_dir / "coverage.xml"
        cmd = [
            "pytest",
            "--cov=.",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing" # Also show in terminal
        ]

        try:
            # We assume the user has installed dependencies including pytest-cov
            subprocess.run(cmd, cwd=project_dir, check=False) # Don't check=True as tests might fail
            if xml_report.exists():
                return xml_report
            else:
                print("❌ Warning: coverage.xml was not generated. Is pytest-cov installed?")
                return None
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return None

    # 2. Node.js (Jest/Vitest) - Placeholder logic
    # Requires configuration in package.json usually
    elif (project_dir / "package.json").exists():
        print("Detected Node.js project. Attempting to run coverage...")
        # Check for coverage script or standard jest/vitest flags
        # This is a best-effort guess
        cmd = ["npm", "test", "--", "--coverage"]
        try:
            subprocess.run(cmd, cwd=project_dir, check=False)
            # Check for common coverage report locations
            possible_reports = [
                project_dir / "coverage/cobertura-coverage.xml",
                project_dir / "coverage/clover.xml" # Clover is XML but schema differs slightly, parse_xml might need tweak or use generic parsing
            ]
            for rep in possible_reports:
                if rep.exists():
                    return rep
            return None
        except Exception:
            pass

    # 3. Go
    elif (project_dir / "go.mod").exists():
        print("Detected Go project. Running go test -cover...")
        # Go coverage is usually a simple text file, not XML by default unless converted
        # Implementing basic go support requires `gocov-xml` or parsing the text profile.
        # For this iteration, we'll skip complex Go parsing and just run the command.
        cmd = ["go", "test", "-coverprofile=coverage.out", "./..."]
        try:
            subprocess.run(cmd, cwd=project_dir, check=False)
            print("✅ Go coverage run. Parsing 'coverage.out' is not yet supported in this viewer.")
            return None
        except Exception:
            pass

    print("Could not detect a supported project type for coverage.")
    return None

def display_coverage_report(stats: list[CoverageStats]):
    """Displays a formatted coverage table."""
    if not stats:
        print("No coverage data found.")
        return

    # Sort by percentage (ascending) to show problematic files first
    stats.sort(key=lambda x: x.percent)

    print("\n--- Code Coverage Report ---")
    header = f"{'File':<50} | {'Stmts':<8} | {'Miss':<8} | {'Cover':<8}"
    print(header)
    print("-" * len(header))

    total_stmts = 0
    total_miss = 0

    for s in stats:
        total_stmts += s.statements
        total_miss += s.missed

        color = get_coverage_color(s.percent)
        reset = "\033[0m"

        # Truncate filename if too long
        fname = s.file
        if len(fname) > 48:
            fname = "..." + fname[-45:]

        print(f"{fname:<50} | {s.statements:<8} | {s.missed:<8} | {color}{s.percent:6.2f}%{reset}")

    print("-" * len(header))

    if total_stmts > 0:
        total_percent = ((total_stmts - total_miss) / total_stmts) * 100
        color = get_coverage_color(total_percent)
        reset = "\033[0m"
        print(f"{'TOTAL':<50} | {total_stmts:<8} | {total_miss:<8} | {color}{total_percent:6.2f}%{reset}")
    else:
        print("No statements found.")

def _run_coverage_logic(project_dir: Path):
    """Orchestrates the coverage workflow."""
    xml_report = run_tests_with_coverage(project_dir)

    if xml_report:
        print(f"\nParsing coverage report: {xml_report.name}")
        stats = parse_coverage_xml(xml_report)
        display_coverage_report(stats)
