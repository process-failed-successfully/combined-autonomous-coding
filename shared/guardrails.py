"""
Guardrails (Policy Enforcement) Engine
======================================

Enforces project-specific structural and quality rules.
"""

import abc
import re
import fnmatch
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.complexity import analyze_project_complexity

class Violation:
    def __init__(self, policy_name: str, message: str, file: Optional[str] = None, line: Optional[int] = None):
        self.policy_name = policy_name
        self.message = message
        self.file = file
        self.line = line

    def to_dict(self):
        return {
            "policy": self.policy_name,
            "message": self.message,
            "file": self.file,
            "line": self.line
        }

class Policy(abc.ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abc.abstractmethod
    def check(self, project_dir: Path) -> List[Violation]:
        pass

    def _matches_file(self, file_path: Path, project_dir: Path) -> bool:
        """Checks if the file matches the 'files' and 'exclude' patterns in the config."""
        rel_path = str(file_path.relative_to(project_dir))

        include_pattern = self.config.get("files", "**/*")
        exclude_pattern = self.config.get("exclude")

        # fnmatch isn't great for recursive globbing with **, using Path.match or manual glob checking might be better
        # But simple fnmatch usually works for basic cases.
        # Better approach: Use python's glob to find relevant files first, then filter.

        # However, here we are given a specific file usually.
        # Let's assume standard glob syntax for include/exclude.

        matches_include = file_path.match(include_pattern) or fnmatch.fnmatch(rel_path, include_pattern)

        if not matches_include:
            return False

        if exclude_pattern:
            if file_path.match(exclude_pattern) or fnmatch.fnmatch(rel_path, exclude_pattern):
                return False

        return True

class NamingPolicy(Policy):
    """Enforces naming conventions on files and directories."""

    def check(self, project_dir: Path) -> List[Violation]:
        violations = []
        rules = self.config.get("rules", [])
        files_pattern = self.config.get("files", "**/*")

        # Find all files matching the pattern
        for file_path in project_dir.glob(files_pattern):
            if not self._matches_file(file_path, project_dir):
                continue

            for rule in rules:
                pattern = rule.get("pattern")
                scope = rule.get("scope", "file") # file, directory
                message = rule.get("message", "Naming convention violation")

                if not pattern:
                    continue

                target = file_path.name
                if scope == "directory":
                    target = file_path.parent.name

                if not re.match(pattern, target):
                    violations.append(Violation(self.name, f"{message}: {target} does not match {pattern}", str(file_path.relative_to(project_dir))))

        return violations

class StructurePolicy(Policy):
    """Enforces existence of specific files in directories."""

    def check(self, project_dir: Path) -> List[Violation]:
        violations = []
        target_path_str = self.config.get("path", ".")
        required_files = self.config.get("required_files", [])

        target_path = project_dir / target_path_str

        if not target_path.exists():
             violations.append(Violation(self.name, f"Target path '{target_path_str}' does not exist"))
             return violations

        # If target path is a glob, we iterate over matches
        # But usually structure policy targets specific directories.
        # Let's support simple directory targeting.

        if not target_path.is_dir():
             # If user pointed to a file, maybe ignore?
             return []

        # Iterate over subdirectories if 'recursive' is set?
        # For now, let's just check the target directory.

        for req in required_files:
            if not (target_path / req).exists():
                violations.append(Violation(self.name, f"Missing required file: {req}", str(target_path.relative_to(project_dir))))

        return violations

class ContentPolicy(Policy):
    """Enforces regex patterns within file content."""

    def check(self, project_dir: Path) -> List[Violation]:
        violations = []
        files_pattern = self.config.get("files", "**/*")
        banned_patterns = self.config.get("banned_patterns", [])
        required_patterns = self.config.get("required_patterns", [])

        for file_path in project_dir.glob(files_pattern):
            if not file_path.is_file():
                continue
            if not self._matches_file(file_path, project_dir):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Check banned patterns
            for pattern in banned_patterns:
                match = re.search(pattern, content)
                if match:
                    # Find line number
                    lineno = content[:match.start()].count('\n') + 1
                    violations.append(Violation(self.name, f"Found banned pattern: {pattern}", str(file_path.relative_to(project_dir)), lineno))

            # Check required patterns
            for pattern in required_patterns:
                if not re.search(pattern, content):
                    violations.append(Violation(self.name, f"Missing required pattern: {pattern}", str(file_path.relative_to(project_dir))))

        return violations

class MetricPolicy(Policy):
    """Enforces code metrics (complexity, size)."""

    def check(self, project_dir: Path) -> List[Violation]:
        violations = []
        metric_type = self.config.get("metric")
        max_val = self.config.get("max")

        if metric_type == "complexity":
            # Use shared.complexity
            # Complexity analysis scans all python files by default, filtering logic inside might be needed
            # Or we filter results.

            all_results = analyze_project_complexity(project_dir)

            for res in all_results:
                # res is {file, function, complexity, lineno}
                file_path = project_dir / res["file"]

                if not self._matches_file(file_path, project_dir):
                    continue

                if res["complexity"] > max_val:
                    violations.append(Violation(
                        self.name,
                        f"Complexity {res['complexity']} exceeds max {max_val} in function '{res['function']}'",
                        res["file"],
                        res["lineno"]
                    ))

        elif metric_type == "lines":
            files_pattern = self.config.get("files", "**/*")
            for file_path in project_dir.glob(files_pattern):
                if not file_path.is_file(): continue
                if not self._matches_file(file_path, project_dir): continue

                try:
                    lines = sum(1 for _ in open(file_path, 'rb'))
                    if lines > max_val:
                        violations.append(Violation(self.name, f"File length {lines} exceeds max {max_val} lines", str(file_path.relative_to(project_dir))))
                except Exception:
                    pass

        return violations

class GuardrailsManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.policies: List[Policy] = []
        self.load_config()

    def load_config(self):
        # Look for guardrails.yaml or agent_config.yaml
        config_data = []

        guardrails_path = self.project_dir / "guardrails.yaml"
        agent_config_path = self.project_dir / "agent_config.yaml"

        if guardrails_path.exists():
            try:
                with open(guardrails_path, "r") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, list):
                        config_data = data
                    elif isinstance(data, dict) and "guardrails" in data:
                        config_data = data["guardrails"]
            except Exception as e:
                print(f"Error loading guardrails.yaml: {e}")

        elif agent_config_path.exists():
            try:
                with open(agent_config_path, "r") as f:
                    data = yaml.safe_load(f)
                    config_data = data.get("guardrails", [])
            except Exception as e:
                print(f"Error loading agent_config.yaml: {e}")

        # Instantiate policies
        for p_conf in config_data:
            p_type = p_conf.get("type")
            name = p_conf.get("name", "Unnamed Policy")

            if p_type == "naming":
                self.policies.append(NamingPolicy(name, p_conf))
            elif p_type == "structure":
                self.policies.append(StructurePolicy(name, p_conf))
            elif p_type == "content":
                self.policies.append(ContentPolicy(name, p_conf))
            elif p_type == "metric":
                self.policies.append(MetricPolicy(name, p_conf))

    def run(self) -> List[Violation]:
        all_violations = []
        for policy in self.policies:
            try:
                violations = policy.check(self.project_dir)
                all_violations.extend(violations)
            except Exception as e:
                print(f"Error running policy '{policy.name}': {e}")
                all_violations.append(Violation(policy.name, f"Policy Execution Error: {e}"))

        return all_violations

    def create_default_config(self) -> Path:
        """Creates a default guardrails.yaml if none exists."""
        path = self.project_dir / "guardrails.yaml"
        if path.exists():
            return path

        default_config = [
            {
                "name": "Python Naming",
                "type": "naming",
                "files": "**/*.py",
                "rules": [
                    {"pattern": "^[a-z_][a-z0-9_]*$", "scope": "file", "message": "Python files must be snake_case"}
                ]
            },
            {
                "name": "No Print Statements",
                "type": "content",
                "files": "**/*.py",
                "exclude": "scripts/**",
                "banned_patterns": ["print\\("]
            },
            {
                "name": "Complexity Limit",
                "type": "metric",
                "metric": "complexity",
                "files": "**/*.py",
                "max": 15
            }
        ]

        with open(path, "w") as f:
            yaml.dump(default_config, f, sort_keys=False)

        return path
