import os
import sys
from pathlib import Path
from typing import Dict, Any, List

class CodeStatsManager:
    """
    Analyzes codebase statistics (LOC, comments, blanks).
    """

    # Language definitions: extensions and comment styles
    LANGUAGES = {
        "Python": {"ext": [".py"], "comment": "#"},
        "JavaScript": {"ext": [".js", ".jsx", ".mjs", ".cjs"], "comment": "//"},
        "TypeScript": {"ext": [".ts", ".tsx"], "comment": "//"},
        "HTML": {"ext": [".html", ".htm"], "comment": "<!--"}, # simplified
        "CSS": {"ext": [".css"], "comment": "/*"}, # simplified
        "SCSS": {"ext": [".scss"], "comment": "//"},
        "JSON": {"ext": [".json"], "comment": None},
        "YAML": {"ext": [".yaml", ".yml"], "comment": "#"},
        "Markdown": {"ext": [".md"], "comment": "<!--"},
        "Shell": {"ext": [".sh", ".bash", ".zsh"], "comment": "#"},
        "Dockerfile": {"ext": ["Dockerfile", ".dockerfile"], "comment": "#"},
        "SQL": {"ext": [".sql"], "comment": "--"},
        "Go": {"ext": [".go"], "comment": "//"},
        "Rust": {"ext": [".rs"], "comment": "//"},
        "Java": {"ext": [".java"], "comment": "//"},
        "C": {"ext": [".c", ".h"], "comment": "//"},
        "C++": {"ext": [".cpp", ".hpp", ".cc"], "comment": "//"},
        "Text": {"ext": [".txt"], "comment": None},
    }

    def __init__(self, project_dir: Path, exclude: List[str] = None):
        self.project_dir = project_dir.resolve()
        self.exclude = exclude or []

    def scan(self) -> Dict[str, Dict[str, int]]:
        """
        Scans the project directory and returns stats per language.
        Returns: { "Python": { "files": 10, "lines": 1000, "code": 800, "comment": 100, "blank": 100 } }
        """
        stats = {}

        # Initialize stats
        for lang in self.LANGUAGES:
            stats[lang] = {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}
        stats["Unknown"] = {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}

        # Build extension map for fast lookup
        ext_map = {}
        for lang, info in self.LANGUAGES.items():
            for ext in info["ext"]:
                ext_map[ext] = lang

        # Walk
        for root, dirs, files in os.walk(self.project_dir):
            # Skip hidden dirs (like .git, .venv) and excluded dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in self.exclude]

            for file in files:
                if file.startswith("."): continue

                path = Path(root) / file

                # Determine language
                lang = "Unknown"
                if file in ext_map: # Exact match (e.g. Dockerfile)
                    lang = ext_map[file]
                elif path.suffix in ext_map:
                    lang = ext_map[path.suffix]

                if lang == "Unknown":
                    # Try to detect by shebang for scripts without extension?
                    # For now skip or count as Unknown
                    pass

                self._count_file(path, lang, stats)

        # Remove empty languages
        return {k: v for k, v in stats.items() if v["files"] > 0}

    def _count_file(self, path: Path, lang: str, stats: Dict[str, Any]):
        try:
            # Skip binary files check - naive approach: try reading as utf-8
            try:
                content = path.read_text(encoding="utf-8", errors="strict")
            except UnicodeDecodeError:
                return # Likely binary

            lines = content.splitlines()
            total = len(lines)
            blank = 0
            comment = 0
            code = 0

            comment_char = None
            if lang in self.LANGUAGES:
                comment_char = self.LANGUAGES[lang]["comment"]

            in_block_comment = False # For C-style, not implementing full parser yet

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank += 1
                    continue

                if comment_char and stripped.startswith(comment_char):
                    comment += 1
                    continue

                # Naive C-style block comment detection (very basic)
                if lang in ["JavaScript", "TypeScript", "Java", "C", "C++", "CSS", "Go", "Rust"]:
                    if stripped.startswith("/*") and stripped.endswith("*/"):
                        comment += 1
                        continue
                    if stripped.startswith("/*"):
                        in_block_comment = True
                        comment += 1
                        continue
                    if in_block_comment:
                        comment += 1
                        if "*/" in stripped:
                            in_block_comment = False
                        continue

                code += 1

            stats[lang]["files"] += 1
            stats[lang]["lines"] += total
            stats[lang]["code"] += code
            stats[lang]["comment"] += comment
            stats[lang]["blank"] += blank

        except Exception as e:
            # print(f"Error counting {path}: {e}", file=sys.stderr)
            pass

def run_stats_lab_logic(args):
    """CLI logic for Stats Lab."""
    from rich.console import Console
    from rich.table import Table
    from shared.charts import draw_ascii_bar_chart

    project_dir = args.project_dir.resolve()
    exclude = getattr(args, "exclude", [])
    manager = CodeStatsManager(project_dir, exclude=exclude)

    if exclude:
        print(f"Scanning {project_dir}... (excluding: {', '.join(exclude)})")
    else:
        print(f"Scanning {project_dir}...")
    stats = manager.scan()

    if args.format == "json":
        import json
        print(json.dumps(stats, indent=2))
        sys.exit(0)

    console = Console()

    # 1. Distribution Chart
    loc_data = {lang: info["code"] for lang, info in stats.items()}
    # Sort by code lines desc
    loc_data = dict(sorted(loc_data.items(), key=lambda item: item[1], reverse=True))

    if loc_data:
        chart = draw_ascii_bar_chart(loc_data, "Lines of Code by Language", width=50)
        print("\n" + chart + "\n")

    # 2. Detailed Table
    table = Table(title="Codebase Statistics")
    table.add_column("Language", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Lines", justify="right")
    table.add_column("Code", justify="right", style="green")
    table.add_column("Comments", justify="right", style="yellow")
    table.add_column("Blanks", justify="right", style="dim")

    # Calculate totals
    totals = {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}

    for lang, info in loc_data.items(): # Use sorted order
        full_info = stats[lang]
        table.add_row(
            lang,
            str(full_info["files"]),
            str(full_info["lines"]),
            str(full_info["code"]),
            str(full_info["comment"]),
            str(full_info["blank"])
        )
        for k in totals:
            totals[k] += full_info[k]

    table.add_section()
    table.add_row(
        "TOTAL",
        str(totals["files"]),
        str(totals["lines"]),
        str(totals["code"]),
        str(totals["comment"]),
        str(totals["blank"]),
        style="bold"
    )

    console.print(table)
    sys.exit(0)
