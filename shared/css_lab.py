import sys
import re
from pathlib import Path


class CssLabManager:
    def minify(self, css_content: str) -> str:
        """Minifies CSS content by removing comments and unnecessary whitespace."""
        # Remove comments
        css = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        # Remove whitespace around structural characters
        css = re.sub(r'\s*([\{\}\:\;\>\,])\s*', r'\1', css)
        # Remove trailing semicolons in blocks
        css = re.sub(r';\}', '}', css)
        # Remove newlines and compress spaces
        css = re.sub(r'\s+', ' ', css)
        return css.strip()

    def format(self, css_content: str, indent: int = 2) -> str:
        """Formats CSS content to be human-readable."""
        # First minify to standardize everything
        css = self.minify(css_content)

        # Prepare tokens
        # Add newlines around {, }, and ;
        css = css.replace('{', ' {\n')
        css = css.replace('}', '\n}\n\n')
        css = css.replace(';', ';\n')

        lines = css.split('\n')
        output = []
        depth = 0
        indent_str = ' ' * indent

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line == '}':
                depth = max(0, depth - 1)
                output.append((indent_str * depth) + line)
            elif line.endswith('{'):
                output.append((indent_str * depth) + line)
                depth += 1
            else:
                output.append((indent_str * depth) + line)

        return '\n'.join(output).strip() + '\n'


def run_css_lab_logic(args):
    """CLI logic for css-lab."""
    if getattr(args, 'action', None) == 'tui':
        from shared.tui import AgentTUI
        print("Launching CSS Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, "project_dir", Path(".")), start_tab="tab-css")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        sys.exit(0)

    manager = CssLabManager()
    content = ""

    if getattr(args, 'file', None):
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: Input file or stdin required for format/minify.", file=sys.stderr)
            sys.exit(1)

    if args.action == "minify":
        print(manager.minify(content))
    elif args.action == "format":
        print(manager.format(content))
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
