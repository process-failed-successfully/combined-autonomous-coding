from typing import List, Dict, Any, Tuple
import fnmatch
from shared.impact import ImpactAnalyzer
from pathlib import Path

def check_architecture(project_dir: Path, rules: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Checks the project architecture against a set of rules.

    Args:
        project_dir: The root directory of the project.
        rules: A list of dictionaries defining the rules.
               Each rule should have 'source' and 'deny' keys with glob patterns.
               Example: {"source": "shared/**", "deny": "agents/**"}

    Returns:
        A list of violations. Each violation is a dictionary with 'source', 'imported', and 'rule'.
    """
    analyzer = ImpactAnalyzer(project_dir)
    analyzer.build_graph()

    violations = []

    # analyzer.dependencies maps file -> set of imported files
    # keys and values are relative paths strings
    for source_file, imports in analyzer.dependencies.items():
        for imported_file in imports:
            for rule in rules:
                source_pattern = rule.get("source")
                deny_pattern = rule.get("deny")

                if not source_pattern or not deny_pattern:
                    continue

                # Check if source_file matches source_pattern
                # fnmatch doesn't handle ** recursive matching well across versions/platforms as standard glob
                # But python's fnmatch supports * and ?
                # We want globstar behavior usually.
                # Let's assume standard fnmatch for now, but user might need to use "shared/*" or "shared/*/*"
                # Actually, standard fnmatch in python matches against the name, but we can check path.

                # To support recursive directory matching with simple patterns like "shared/*" we might need regex or just rely on fnmatch against the full relative path
                if fnmatch.fnmatch(source_file, source_pattern):
                    if fnmatch.fnmatch(imported_file, deny_pattern):
                        violations.append({
                            "source": source_file,
                            "imported": imported_file,
                            "rule": f"'{source_pattern}' cannot import '{deny_pattern}'"
                        })

    return violations
