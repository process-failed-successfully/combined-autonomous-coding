"""
Risk Analysis Module
====================

Combines code complexity analysis with test coverage data to identify high-risk areas.
Risk Score = Complexity * (1 - Coverage%)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from shared.complexity import analyze_project_complexity

class RiskAnalyzer:
    def __init__(self, project_dir: Path, coverage_xml_path: Optional[Path] = None):
        self.project_dir = project_dir.resolve()
        self.coverage_xml_path = coverage_xml_path
        if not self.coverage_xml_path:
            self.coverage_xml_path = self.project_dir / "coverage.xml"

        self.coverage_data: Dict[str, Dict[str, float]] = {} # file -> {line -> hits}

    def load_coverage(self) -> bool:
        """Parses the coverage XML file."""
        if not self.coverage_xml_path.exists():
            return False

        try:
            tree = ET.parse(self.coverage_xml_path)
            root = tree.getroot()

            # XML format usually has packages -> classes -> lines
            # Filenames in XML might be relative or absolute

            for package in root.findall(".//package"):
                for cls in package.findall(".//class"):
                    filename = cls.get("filename")
                    if not filename:
                        continue

                    # Normalize filename to be relative to project root if possible
                    # Cobertura format often uses relative paths

                    lines = {}
                    for line in cls.findall(".//line"):
                        number = line.get("number")
                        hits = line.get("hits")
                        if number is not None and hits is not None:
                            lines[int(number)] = int(hits)

                    self.coverage_data[filename] = lines
            return True
        except Exception as e:
            print(f"Error parsing coverage XML: {e}")
            return False

    def is_line_covered(self, file_path: str, lineno: int) -> bool:
        """Checks if a specific line is covered."""
        # file_path should match what's in coverage XML
        # We might need fuzzy matching or path normalization

        # Try exact match
        if file_path in self.coverage_data:
            return self.coverage_data[file_path].get(lineno, 0) > 0

        # Try matching by suffix if full path differs
        for key in self.coverage_data:
            if file_path.endswith(key) or key.endswith(file_path):
                return self.coverage_data[key].get(lineno, 0) > 0

        return False

    def calculate_risk(self) -> List[Dict[str, Any]]:
        """Calculates risk scores for all functions in the project."""

        # 1. Get Complexity Data
        complexity_data = analyze_project_complexity(self.project_dir)

        risk_results = []

        for item in complexity_data:
            file_path = item["file"]
            lineno = item["lineno"]
            complexity = item["complexity"]

            # Check coverage for the function definition line
            # Ideally we check the whole body, but line coverage of def is a proxy
            # Better: Check if ANY line in the function is covered?
            # Or assume if def is hit, it's covered?
            # Usually 'def' line is executable.

            is_covered = self.is_line_covered(file_path, lineno)

            # Risk Score Formula
            # If covered: Risk = Complexity * 0.1 (low risk but still complex)
            # If not covered: Risk = Complexity * 1.0 (full risk)

            coverage_factor = 0.1 if is_covered else 1.0
            risk_score = complexity * coverage_factor

            risk_results.append({
                "file": file_path,
                "function": item["function"],
                "lineno": lineno,
                "complexity": complexity,
                "covered": is_covered,
                "risk_score": risk_score
            })

        return sorted(risk_results, key=lambda x: x["risk_score"], reverse=True)

def _run_risk_logic(project_dir: Path, coverage_xml: Optional[Path], threshold: float = 10.0, json_output: bool = False):
    analyzer = RiskAnalyzer(project_dir, coverage_xml)

    if not analyzer.load_coverage():
        print("❌ Error: Could not load coverage data.")
        print(f"   Expected file: {analyzer.coverage_xml_path}")
        print("   Please run tests with coverage first, e.g.:")
        print("     pytest --cov=. --cov-report=xml")
        return

    risks = analyzer.calculate_risk()

    if json_output:
        import json
        print(json.dumps(risks, indent=2))
        return

    print(f"--- Risk Analysis: {project_dir.name} ---")
    print(f"Threshold: {threshold}")

    high_risk_items = [r for r in risks if r["risk_score"] >= threshold]

    if not high_risk_items:
        print("✅ No high-risk functions found.")
        return

    print(f"\nFound {len(high_risk_items)} high-risk functions:\n")

    # Header
    print(f"{'Risk':<8} | {'Compl.':<8} | {'Cov.':<5} | {'File':<40} | {'Function'}")
    print("-" * 85)

    for r in high_risk_items:
        covered_str = "YES" if r["covered"] else "NO"
        file_display = r["file"]
        if len(file_display) > 38:
            file_display = "..." + file_display[-35:]

        print(f"{r['risk_score']:<8.1f} | {r['complexity']:<8} | {covered_str:<5} | {file_display:<40} | {r['function']}:{r['lineno']}")

    print("\nLegend:")
    print("  Risk Score = Complexity * (1.0 if Uncovered, 0.1 if Covered)")
    print("  Target: Test complex functions to reduce risk.")
