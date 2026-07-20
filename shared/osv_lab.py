"""
OSV Lab
=======

Utilities for querying the Open Source Vulnerability (OSV) database.
"""

import sys
import json
import requests
from typing import Dict, Any, Optional


class OsvLabManager:
    """Manages queries to the OSV API."""

    API_URL = "https://api.osv.dev/v1/query"

    def query_package(self, name: str, ecosystem: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries the OSV database for vulnerabilities related to a package.
        """
        payload: Dict[str, Any] = {
            "package": {
                "name": name,
                "ecosystem": ecosystem
            }
        }
        if version:
            payload["version"] = version

        try:
            response = requests.post(self.API_URL, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def format_vulnerability(self, vuln: Dict[str, Any]) -> str:
        """Formats a single vulnerability entry into a readable string."""
        vuln_id = vuln.get("id", "Unknown ID")
        aliases = ", ".join(vuln.get("aliases", []))
        summary = vuln.get("summary", "No summary available")
        details = vuln.get("details", "").strip()

        # Try to find severities
        severity_score = "Unknown"
        severities = vuln.get("severity", [])
        for s in severities:
            if s.get("type") in ["CVSS_V3", "CVSS_V4"]:
                severity_score = s.get("score", "Unknown")
                break

        # Try to extract affected versions / fixed versions
        affected_list = vuln.get("affected", [])
        fixed_versions = []
        for affected in affected_list:
            ranges = affected.get("ranges", [])
            for r in ranges:
                events = r.get("events", [])
                for e in events:
                    if "fixed" in e:
                        fixed_versions.append(e["fixed"])

        fixed_str = ", ".join(fixed_versions) if fixed_versions else "No fix specified"

        output = f"ID: {vuln_id}"
        if aliases:
            output += f" (Aliases: {aliases})"
        output += f"\nSeverity: {severity_score}"
        output += f"\nSummary: {summary}"
        output += f"\nFixed in: {fixed_str}"
        if details:
            # truncate details if too long
            if len(details) > 300:
                details = details[:297] + "..."
            output += f"\nDetails: {details}"
        output += "\n" + "-" * 40
        return output


def run_osv_lab_logic(args):
    """CLI logic for OSV Lab."""
    manager = OsvLabManager()

    if getattr(args, "tui", False):
        from main import run_tui
        run_tui("tab-osv-lab")
        sys.exit(0)

    name = args.package
    ecosystem = args.ecosystem
    version = getattr(args, "version", None)

    if not name or not ecosystem:
        print("Error: Both --package and --ecosystem are required for CLI query.", file=sys.stderr)
        sys.exit(1)

    result = manager.query_package(name, ecosystem, version)

    if "error" in result:
        print(f"Error querying OSV API: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return

    vulns = result.get("vulns", [])
    if not vulns:
        if version:
            print(f"✅ No known vulnerabilities found for {name} ({ecosystem}) version {version}.")
        else:
            print(f"✅ No known vulnerabilities found for {name} ({ecosystem}).")
        return

    print(f"⚠️ Found {len(vulns)} vulnerabilities for {name} ({ecosystem}):\n")
    for vuln in vulns:
        print(manager.format_vulnerability(vuln))

    return
