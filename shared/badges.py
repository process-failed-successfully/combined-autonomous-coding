import sys
import re
import json
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
from shared.todos import scan_todos
from shared.verify import run_command

@dataclass
class Badge:
    label: str
    message: str
    color: str
    link: Optional[str] = None

    def to_markdown(self) -> str:
        # Shields.io format: https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>
        # We need to escape underscores and dashes in label/message
        safe_label = self.label.replace("-", "--").replace("_", "__").replace(" ", "_")
        safe_message = self.message.replace("-", "--").replace("_", "__").replace(" ", "_")
        url = f"https://img.shields.io/badge/{safe_label}-{safe_message}-{self.color}"

        md = f"![{self.label}]({url})"
        if self.link:
            md = f"[{md}]({self.link})"
        return md

class BadgeManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def generate_badges(self) -> List[Badge]:
        badges = []

        # 1. Tests & Coverage
        test_badge = self._get_test_badge()
        if test_badge:
            badges.append(test_badge)

        # 2. Linting
        lint_badge = self._get_lint_badge()
        if lint_badge:
            badges.append(lint_badge)

        # 3. Security
        sec_badge = self._get_security_badge()
        if sec_badge:
            badges.append(sec_badge)

        # 4. TODOs
        todo_badge = self._get_todo_badge()
        if todo_badge:
            badges.append(todo_badge)

        return badges

    def _get_test_badge(self) -> Optional[Badge]:
        # Check if pytest is available
        if not shutil.which("pytest"):
            return None

        # Run pytest with coverage
        print("Running tests for badge generation...")
        cmd = ["pytest", "--cov=.", "--cov-report=term-missing", "tests/"]

        # We assume pytest is configured or available in env
        # If running in agent env, we might need to be careful about long running tests
        # For now, we run it.
        result = run_command(cmd, self.project_dir)

        if result.returncode != 0:
            return Badge("tests", "failing", "red")

        # Parse coverage from stdout
        # Look for "TOTAL ... 85%"
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
        if match:
            cov = int(match.group(1))
            color = "green" if cov >= 80 else "yellow" if cov >= 50 else "red"
            return Badge("coverage", f"{cov}%", color)

        return Badge("tests", "passing", "green")

    def _get_lint_badge(self) -> Optional[Badge]:
        if not shutil.which("flake8"):
            return None

        print("Running lint for badge generation...")

        # verify.py splits it into two passes. We'll do a simple count pass.
        # "flake8 . --count --exit-zero --statistics"
        cmd = ["flake8", ".", "--count", "--exit-zero", "--exclude=.venv,venv,build,dist"]
        result = run_command(cmd, self.project_dir)

        try:
            # The last line should be the count
            lines = result.stdout.strip().splitlines()
            if not lines:
                return Badge("lint", "unknown", "lightgrey")

            count = int(lines[-1])
            color = "green" if count == 0 else "yellow" if count < 10 else "red"
            return Badge("lint", f"{count} issues", color)
        except ValueError:
            return Badge("lint", "error", "lightgrey")

    def _get_security_badge(self) -> Optional[Badge]:
        if not shutil.which("bandit"):
            return None

        print("Running security scan for badge generation...")
        # Use --quiet to avoid logs in stdout (though they should be in stderr)
        cmd = ["bandit", "--quiet", "-r", ".", "-f", "json", "-x", ".venv,venv,build,tests"]
        result = run_command(cmd, self.project_dir)

        try:
            data = json.loads(result.stdout)
            metrics = data.get("metrics", {}).get("_totals", {})
            high = metrics.get("CONFIDENCE.HIGH", 0) + metrics.get("SEVERITY.HIGH", 0)
            medium = metrics.get("CONFIDENCE.MEDIUM", 0) + metrics.get("SEVERITY.MEDIUM", 0)

            # Bandit JSON structure is a bit complex. "results" is a list of issues.
            issues = data.get("results", [])
            high_severity = sum(1 for i in issues if i["issue_severity"] == "HIGH")
            medium_severity = sum(1 for i in issues if i["issue_severity"] == "MEDIUM")

            if high_severity > 0:
                return Badge("security", f"{high_severity} high", "red")
            elif medium_severity > 0:
                return Badge("security", f"{medium_severity} medium", "yellow")
            else:
                return Badge("security", "secure", "green")

        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    def _get_todo_badge(self) -> Badge:
        print("Scanning TODOs for badge generation...")
        # scan_todos returns a list of dicts
        todos = scan_todos(self.project_dir)
        count = len(todos)
        color = "green" if count == 0 else "blue" if count < 20 else "orange"
        return Badge("todos", str(count), color)

    def update_readme(self, badges: List[Badge]) -> bool:
        readme_path = self.project_dir / "README.md"
        if not readme_path.exists():
            print("README.md not found.", file=sys.stderr)
            return False

        content = readme_path.read_text(encoding="utf-8")

        badge_md = " ".join([b.to_markdown() for b in badges])
        section = f"<!-- BADGES_START -->\n{badge_md}\n<!-- BADGES_END -->"

        # Check if section exists
        pattern = r"<!-- BADGES_START -->.*<!-- BADGES_END -->"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, section, content, flags=re.DOTALL)
        else:
            # Prepend to file (after title usually, but checking for title is hard)
            # We'll just put it at the top or after the first header
            lines = content.splitlines()
            if lines and lines[0].startswith("#"):
                # Insert after first line
                lines.insert(1, "\n" + section)
                new_content = "\n".join(lines)
            else:
                new_content = section + "\n\n" + content

        readme_path.write_text(new_content, encoding="utf-8")
        return True

def run_badges_logic(args):
    """
    CLI Entry point for badges command.
    """
    project_dir = args.project_dir.resolve()
    manager = BadgeManager(project_dir)

    badges = manager.generate_badges()

    if args.json:
        output = [
            {"label": b.label, "message": b.message, "color": b.color, "markdown": b.to_markdown()}
            for b in badges
        ]
        print(json.dumps(output, indent=2))
        return

    print("--- Generated Badges ---")
    for b in badges:
        print(b.to_markdown())

    if args.update_readme:
        if manager.update_readme(badges):
            print("\n✅ README.md updated with badges.")
        else:
            print("\n❌ Failed to update README.md.")
