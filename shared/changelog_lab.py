import subprocess
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import datetime

class ChangelogManager:
    """Manages generating changelogs from git history."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def get_commits(self, start_ref: str, end_ref: str) -> List[Dict[str, str]]:
        """
        Fetches commits between start_ref and end_ref.
        If start_ref is empty, gets all commits up to end_ref.
        Returns a list of dictionaries with commit info.
        """
        rev_range = f"{start_ref}..{end_ref}" if start_ref else end_ref

        # format: hash|author|date|message
        cmd = ["git", "-C", str(self.project_dir), "log", "--pretty=format:%h|%an|%ad|%s", "--date=short", rev_range]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3].strip()
                    })
            return commits
        except subprocess.CalledProcessError as e:
            # Maybe the refs are invalid
            raise ValueError(f"Git command failed: {e.stderr.strip()}")

    def parse_commit_message(self, message: str) -> Tuple[str, str]:
        """
        Extracts conventional commit type and the rest of the message.
        """
        parts = message.split(':', 1)
        if len(parts) == 2:
            ctype = parts[0].split('(')[0].strip().lower()
            return ctype, parts[1].strip()
        return "other", message.strip()

    def generate_changelog(self, start_ref: str, end_ref: str, version: str) -> str:
        """
        Generates markdown changelog text.
        """
        commits = self.get_commits(start_ref, end_ref)

        categories = {
            'feat': '## ✨ Features',
            'fix': '## 🐛 Bug Fixes',
            'docs': '## 📚 Documentation',
            'refactor': '## ♻️ Refactoring',
            'perf': '## ⚡ Performance Improvements',
            'test': '## 🚨 Tests',
            'build': '## 🛠 Build System',
            'ci': '## ⚙️ CI/CD',
            'chore': '## 🧹 Chores',
            'other': '## 📦 Other Changes'
        }

        grouped_commits = {k: [] for k in categories.keys()}

        for commit in commits:
            ctype, msg = self.parse_commit_message(commit['message'])
            if ctype not in grouped_commits:
                ctype = 'other'

            entry = f"- {msg} (`{commit['hash']}` by {commit['author']})"
            grouped_commits[ctype].append(entry)

        today = datetime.date.today().isoformat()
        changelog = [f"# v{version} ({today})\n"]

        for ctype, title in categories.items():
            if grouped_commits[ctype]:
                changelog.append(f"{title}")
                changelog.extend(grouped_commits[ctype])
                changelog.append("") # empty line

        if len(changelog) == 1:
            changelog.append("No changes found in this range.\n")

        return "\n".join(changelog)


def run_changelog_lab_logic(args: argparse.Namespace) -> bool:
    """CLI Entry point for Changelog Lab."""

    project_dir = getattr(args, "project_dir", Path(".")).resolve()
    manager = ChangelogManager(project_dir)

    if args.action == "generate":
        try:
            start_ref = args.base or ""
            end_ref = args.head or "HEAD"
            version = args.version or end_ref

            markdown = manager.generate_changelog(start_ref, end_ref, version)

            if args.output:
                out_path = Path(args.output)
                out_path.write_text(markdown)
                print(f"✅ Changelog saved to {out_path}")
            else:
                print(markdown)
            return True

        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return False

    return False
