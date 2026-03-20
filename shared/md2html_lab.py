import sys
from pathlib import Path
from markdown_it import MarkdownIt

class Md2HtmlManager:
    def __init__(self):
        self.md = MarkdownIt()

    def convert(self, markdown_text: str) -> str:
        return self.md.render(markdown_text)

def run_md2html_logic(args):
    manager = Md2HtmlManager()

    md_content = None

    if getattr(args, "file", None):
        try:
            path = Path(args.file)
            md_content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        md_content = args.text
    elif not sys.stdin.isatty():
        md_content = sys.stdin.read()

    if not md_content:
        print("Error: No Markdown input provided.", file=sys.stderr)
        return False

    html_output = manager.convert(md_content)

    if getattr(args, "output", None):
        try:
            Path(args.output).write_text(html_output, encoding="utf-8")
            print(f"✅ HTML saved to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}", file=sys.stderr)
            return False
    else:
        print(html_output)

    return True
