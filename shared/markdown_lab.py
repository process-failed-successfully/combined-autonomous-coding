import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

class MarkdownLabManager:
    """
    Manages Markdown utilities: TOC generation, stats, table formatting, linting.
    """

    def __init__(self):
        pass

    def generate_toc(self, text: str, depth: int = 3) -> str:
        """
        Generates a Table of Contents from markdown text.
        """
        toc = []
        # Regex to match headers. Capture level (#s) and title.
        # Use multiline mode.
        headers = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)

        if not headers:
            return ""

        for level_str, title in headers:
            level = len(level_str)
            if level > depth:
                continue

            # Simple slugification
            slug = title.lower()
            slug = re.sub(r'[^\w\s-]', '', slug) # Remove non-word chars except space and hyphen
            slug = re.sub(r'[\s]+', '-', slug)   # Replace spaces with hyphens
            slug = slug.strip('-')

            indent = "  " * (level - 1)
            toc.append(f"{indent}- [{title}](#{slug})")

        return "\n".join(toc)

    def insert_toc(self, text: str, toc: str) -> str:
        """
        Inserts TOC into text. Looks for <!-- TOC --> placeholder.
        If not found, prepends to text (after first h1 if exists, else top).
        """
        marker = "<!-- TOC -->"
        if marker in text:
            return text.replace(marker, f"{marker}\n\n{toc}")

        # Try to insert after first H1
        match = re.search(r'^#\s+.+\n', text, re.MULTILINE)
        if match:
            end_pos = match.end()
            return text[:end_pos] + f"\n## Table of Contents\n\n{toc}\n\n" + text[end_pos:]

        # Prepend to top
        return f"# Table of Contents\n\n{toc}\n\n" + text

    def get_stats(self, text: str) -> Dict[str, Any]:
        """
        Returns statistics about the markdown text.
        """
        words = len(text.split())
        reading_time_min = round(words / 200, 1) if words > 0 else 0

        headers = len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE))
        # Use negative lookbehind to avoid matching images (![...]) as links
        links = len(re.findall(r'(?<!!)\[.*?\]\(.*?\)', text))
        images = len(re.findall(r'!\[.*?\]\(.*?\)', text))
        code_blocks = len(re.findall(r'```', text)) // 2 # Rough estimate

        return {
            "words": words,
            "reading_time_min": reading_time_min,
            "headers": headers,
            "links": links,
            "images": images,
            "code_blocks": code_blocks
        }

    def format_table(self, text: str) -> str:
        """
        Formats markdown tables in the text.
        Identifies tables by looking for pipe characters and separator rows.
        """
        lines = text.splitlines()
        new_lines = []
        in_table = False
        table_buffer = []

        def process_table(buffer):
            if not buffer: return []

            # Parse table
            rows = []
            for line in buffer:
                # remove leading/trailing pipes for splitting if present, but keep structure
                # This is tricky as markdown tables can be messy.
                # Standard: | col1 | col2 |
                # Minimal: col1 | col2

                # We'll split by pipe
                cells = [c.strip() for c in line.strip('|').split('|')]
                rows.append(cells)

            if not rows: return buffer

            # Calculate widths
            col_widths = {}
            num_cols = max(len(r) for r in rows)

            # Normalize rows
            for r in rows:
                while len(r) < num_cols:
                    r.append("")

            for r_idx, row in enumerate(rows):
                for c_idx, cell in enumerate(row):
                    # Check if separator row
                    if r_idx == 1 and re.match(r'^[-:\s]+$', cell):
                        # It's a separator, min width 3
                        width = max(3, len(cell))
                    else:
                        width = len(cell)

                    col_widths[c_idx] = max(col_widths.get(c_idx, 0), width)

            # Reconstruct
            formatted_rows = []
            for r_idx, row in enumerate(rows):
                formatted_cells = []
                for c_idx, cell in enumerate(row):
                    width = col_widths[c_idx]
                    if r_idx == 1:
                        # Separator logic
                        # Detect alignment from original cell
                        if cell.startswith(':') and cell.endswith(':'):
                            new_cell = ':' + '-' * (width - 2) + ':'
                        elif cell.endswith(':'):
                            new_cell = '-' * (width - 1) + ':'
                        elif cell.startswith(':'):
                            new_cell = ':' + '-' * (width - 1)
                        else:
                            new_cell = '-' * width
                        formatted_cells.append(new_cell)
                    else:
                        formatted_cells.append(cell.ljust(width))

                formatted_rows.append(f"| {' | '.join(formatted_cells)} |")

            return formatted_rows

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Simple heuristic for table line: contains pipe
            if "|" in stripped:
                # Check if it looks like a table line (not just text with pipe)
                # Usually table lines start or end with pipe, or contain multiple pipes
                # and are surrounded by other table lines.
                # We'll look for the separator line to confirm table structure.
                # For now, let's assume contiguous lines with pipes are a table block
                # if there is at least one separator line in the block.
                table_buffer.append(line)
            else:
                if table_buffer:
                    # Check if buffer is valid table (has separator line)
                    # Fixed regex: escaped hyphen
                    has_separator = any(re.match(r'^\s*\|?[\s\-:]+\|[\s\-:|]+\s*$', l) for l in table_buffer)
                    if has_separator:
                        new_lines.extend(process_table(table_buffer))
                    else:
                        new_lines.extend(table_buffer)
                    table_buffer = []
                new_lines.append(line)

        # Flush buffer
        if table_buffer:
             has_separator = any(re.match(r'^\s*\|?[\s\-:]+\|[\s\-:|]+\s*$', l) for l in table_buffer)
             if has_separator:
                 new_lines.extend(process_table(table_buffer))
             else:
                 new_lines.extend(table_buffer)

        return "\n".join(new_lines)

    def lint(self, text: str, root_dir: Path = None) -> List[Dict[str, Any]]:
        """
        Lints markdown text.
        """
        issues = []
        lines = text.splitlines()

        # Header hierarchy check
        last_level = 0
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+', line)
            if match:
                level = len(match.group(1))
                if level > last_level + 1 and last_level != 0:
                    issues.append({
                        "line": i + 1,
                        "type": "header-hierarchy",
                        "message": f"Header level jump: h{last_level} -> h{level}"
                    })
                last_level = level

        # Alt text check
        for i, line in enumerate(lines):
            # Find images: ![alt](url)
            for match in re.finditer(r'!\[(.*?)\]\((.*?)\)', line):
                alt_text = match.group(1)
                if not alt_text.strip():
                     issues.append({
                        "line": i + 1,
                        "type": "missing-alt-text",
                        "message": "Image missing alt text"
                    })

        # Local link check
        if root_dir:
            for i, line in enumerate(lines):
                # Find links: [text](url)
                # Ignore images (handled above) - look for [ not preceded by !
                # Regex negative lookbehind is tricky, so let's just match all []() and filter out images manually if needed
                # or simpler: match (src)
                for match in re.finditer(r'(?<!!)\[.*?\]\((.*?)\)', line):
                    link = match.group(1)
                    # Check if local
                    if not link.startswith(('http://', 'https://', 'mailto:', '#')):
                         # It's likely local
                         # remove anchors
                         link_path_str = link.split('#')[0]
                         if not link_path_str: continue

                         # Check existence
                         link_path = (root_dir / link_path_str).resolve()
                         try:
                            if not link_path.exists():
                                issues.append({
                                    "line": i + 1,
                                    "type": "broken-link",
                                    "message": f"Broken local link: {link_path_str}"
                                })
                            # Security check: ensure strictly within root_dir? Maybe too strict for general usage.
                         except OSError:
                             pass # Invalid path

        return issues


def run_markdown_lab_logic(args):
    """
    CLI Handler for Markdown Lab.
    """
    manager = MarkdownLabManager()

    # Helper to get input
    def get_input(file_path):
        if file_path:
            p = Path(file_path)
            if not p.exists():
                 print(f"Error: File {file_path} not found.", file=sys.stderr)
                 return None
            return p.read_text(encoding="utf-8", errors="replace")

        # Try stdin
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read()
            except Exception:
                pass
        return None

    if args.action == "toc":
        text = get_input(args.file)
        if text is None:
            print("Error: Input required (file or stdin).", file=sys.stderr)
            return False

        toc = manager.generate_toc(text, depth=args.depth)

        if args.insert and args.file:
            new_text = manager.insert_toc(text, toc)
            Path(args.file).write_text(new_text, encoding="utf-8")
            print(f"✅ TOC inserted into {args.file}")
        else:
            print(toc)

    elif args.action == "stats":
        text = get_input(args.file)
        if text is None:
            print("Error: Input required (file or stdin).", file=sys.stderr)
            return False

        stats = manager.get_stats(text)
        print("--- Markdown Stats ---")
        print(f"Words: {stats['words']}")
        print(f"Reading Time: {stats['reading_time_min']} min")
        print(f"Headers: {stats['headers']}")
        print(f"Links: {stats['links']}")
        print(f"Images: {stats['images']}")
        print(f"Code Blocks: {stats['code_blocks']}")

    elif args.action == "table":
        text = get_input(args.file)
        if text is None:
            print("Error: Input required (file or stdin).", file=sys.stderr)
            return False

        formatted = manager.format_table(text)

        if args.output:
            Path(args.output).write_text(formatted, encoding="utf-8")
            print(f"✅ Formatted tables saved to {args.output}")
        elif args.file and not args.output:
            # In-place? No, safer to print unless explicit
            print(formatted)
        else:
            print(formatted)

    elif args.action == "lint":
        text = get_input(args.file)
        if text is None:
            print("Error: Input required (file or stdin).", file=sys.stderr)
            return False

        root_dir = Path(args.root).resolve() if args.root else Path.cwd()
        if args.file:
             # If checking links relative to file, root might need adjustment or we use file parent
             root_dir = Path(args.file).parent.resolve()

        issues = manager.lint(text, root_dir)

        if not issues:
            print("✅ No issues found.")
        else:
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"  Line {issue['line']}: [{issue['type']}] {issue['message']}")
            return False

    return True
