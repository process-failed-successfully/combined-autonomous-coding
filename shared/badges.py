import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from shared.security import SecurityAuditor
from shared.todos import scan_todos

class BadgeGenerator:
    """Generates status badges for the project."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _estimate_width(self, text: str) -> int:
        """Estimates the width of text in pixels (approximate)."""
        # A rough heuristic: 7px per character + padding
        return int(len(str(text)) * 7 + 10)

    def generate_badge(self, label: str, value: str, color: str = "#4c1") -> str:
        """Generates an SVG badge."""
        label_width = self._estimate_width(label)
        value_width = self._estimate_width(value)
        total_width = label_width + value_width

        label_x = label_width / 2
        value_x = label_width + (value_width / 2)

        # SVG Template
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <mask id="a"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{value_width}v20H{label_width}z"/>
    <path fill="url(#b)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_x}" y="14">{label}</text>
    <text x="{value_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_x}" y="14">{value}</text>
  </g>
</svg>"""
        return svg

    def get_test_status(self) -> Dict[str, str]:
        """Checks test status based on QA_PASSED file."""
        qa_file = self.project_dir / "QA_PASSED"
        if qa_file.exists():
            return {"value": "passing", "color": "#4c1"}
        return {"value": "unknown", "color": "#9f9f9f"}

    def get_security_count(self) -> Dict[str, str]:
        """Counts high severity security issues."""
        try:
            auditor = SecurityAuditor(self.project_dir)
            findings = auditor.scan_secrets() # Fast scan
            # We could also run SAST but it might be slow. Let's stick to secrets for the "fast" badge.
            # Or maybe we can try to run all if not too slow?
            # Let's just do secrets for now to be safe on performance.
            count = len(findings)
            color = "#4c1" if count == 0 else "#e05d44"
            return {"value": f"{count} issues", "color": color}
        except Exception:
            return {"value": "error", "color": "#9f9f9f"}

    def get_todo_count(self) -> Dict[str, str]:
        """Counts TODOs."""
        try:
            todos = scan_todos(self.project_dir)
            count = len(todos)
            color = "#4c1"
            if count > 0:
                color = "#dfb317" # Yellow
            if count > 10:
                color = "#fe7d37" # Orange

            return {"value": f"{count} pending", "color": color}
        except Exception:
            return {"value": "error", "color": "#9f9f9f"}

    def update_readme(self, badges: Dict[str, str]):
        """Injects badges into README.md."""
        readme_path = self.project_dir / "README.md"
        if not readme_path.exists():
            print("README.md not found. Skipping update.")
            return

        content = readme_path.read_text(encoding="utf-8")

        # Prepare badge HTML
        # We need to save SVGs to a directory or embed them?
        # Usually badges are images linked.
        # If we generate local SVGs, we should link to them relative to repo root.

        badge_html_lines = []
        for name, svg_content in badges.items():
            filename = f"badge_{name.lower()}.svg"
            # Save the SVG
            (self.project_dir / filename).write_text(svg_content, encoding="utf-8")
            badge_html_lines.append(f"![{name}](./{filename})")

        badge_block = " ".join(badge_html_lines)

        start_marker = "<!-- BADGES_START -->"
        end_marker = "<!-- BADGES_END -->"

        if start_marker in content and end_marker in content:
            # Replace existing block
            pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
            replacement = f"{start_marker}\n{badge_block}\n{end_marker}"
            new_content = pattern.sub(replacement, content)
        else:
            # Prepend to file
            new_content = f"{start_marker}\n{badge_block}\n{end_marker}\n\n{content}"

        readme_path.write_text(new_content, encoding="utf-8")
        print("Updated README.md with badges.")

def run_badges_logic(args):
    """CLI logic for badges."""
    project_dir = args.project_dir.resolve()
    generator = BadgeGenerator(project_dir)

    if args.action == "create":
        if not args.label or not args.value:
            print("Error: --label and --value required for create.")
            return False

        svg = generator.generate_badge(args.label, args.value, args.color or "#4c1")

        output = args.output or "badge.svg"
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = project_dir / output_path

        output_path.write_text(svg, encoding="utf-8")
        print(f"✅ Created badge at {output_path}")
        return True

    elif args.action == "generate":
        print(f"Generating badges for {project_dir}...")

        badges = {}

        # Tests
        test_info = generator.get_test_status()
        badges["Tests"] = generator.generate_badge("Tests", test_info["value"], test_info["color"])

        # Security
        sec_info = generator.get_security_count()
        badges["Security"] = generator.generate_badge("Security", sec_info["value"], sec_info["color"])

        # TODOs
        todo_info = generator.get_todo_count()
        badges["TODOs"] = generator.generate_badge("TODOs", todo_info["value"], todo_info["color"])

        # Save individual files if not updating readme or just always save them
        # If --update-readme is passed, we save them and update readme
        if args.update_readme:
            generator.update_readme(badges)
        else:
            # Just save them to current dir
            for name, content in badges.items():
                filename = f"badge_{name.lower()}.svg"
                path = project_dir / filename
                path.write_text(content, encoding="utf-8")
                print(f"Generated {filename}")

        return True

    return False
