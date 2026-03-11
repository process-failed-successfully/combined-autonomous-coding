import argparse
import sys
import re

class CssLabManager:
    def __init__(self):
        pass

    def minify(self, css_text: str) -> str:
        """Minifies CSS text by removing comments and whitespace."""
        # Remove comments
        css = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

        # A more robust minifier approach:
        # We need to strip spaces but protect string literals and calc/var etc.
        # This is a simplified regex-based approach. A full AST parser is best for real CSS minification.

        # 1. Protect strings
        strings = []
        def repl_string(m):
            strings.append(m.group(0))
            return f"__STR_{len(strings)-1}__"

        css = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', repl_string, css)

        # 2. Protect calc(), var(), url() which may need internal spacing
        funcs = []
        def repl_func(m):
            funcs.append(m.group(0))
            return f"__FUNC_{len(funcs)-1}__"

        css = re.sub(r'(calc|var|url)\(.*?\)', repl_func, css)

        # 3. Remove newlines and tabs
        css = re.sub(r'[\r\n\t]+', ' ', css)

        # 4. Remove spaces around structural characters
        css = re.sub(r'\s*([\{\}\:\;\,>+~])\s*', r'\1', css)

        # 5. Remove empty rules
        css = re.sub(r'[^\}]+\{\}', '', css)

        # 6. Remove trailing semicolons in blocks
        css = re.sub(r';\}', '}', css)

        # Restore funcs
        for i, func in reversed(list(enumerate(funcs))):
            css = css.replace(f"__FUNC_{i}__", func)

        # Restore strings
        for i, s in reversed(list(enumerate(strings))):
            css = css.replace(f"__STR_{i}__", s)

        return css.strip()

    def format(self, css_text: str) -> str:
        """Formats CSS text for readability."""
        # To format safely, we first minify to get a baseline
        minified = self.minify(css_text)

        # Protect strings
        strings = []
        def repl_string(m):
            strings.append(m.group(0))
            return f"__STR_{len(strings)-1}__"

        formatted = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', repl_string, minified)

        # Protect functions
        funcs = []
        def repl_func(m):
            funcs.append(m.group(0))
            return f"__FUNC_{len(funcs)-1}__"

        formatted = re.sub(r'(calc|var|url)\(.*?\)', repl_func, formatted)

        # Add spaces and newlines
        formatted = formatted.replace('{', ' {\n    ')
        formatted = formatted.replace('}', '\n}\n\n')
        formatted = formatted.replace(';', ';\n    ')

        # Clean up any trailing spaces and add trailing semicolons if missing
        lines = formatted.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            if line and not line.endswith(';') and not line.endswith('{') and not line.endswith('}') and ':' in line:
                line += ';'
            cleaned_lines.append(line)

        formatted = '\n'.join(cleaned_lines)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)

        # Restore funcs
        for i, func in reversed(list(enumerate(funcs))):
            formatted = formatted.replace(f"__FUNC_{i}__", func)

        # Restore strings
        for i, s in reversed(list(enumerate(strings))):
            formatted = formatted.replace(f"__STR_{i}__", s)

        return formatted.strip()

def run_css_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = CssLabManager()

        if getattr(args, "action") == "minify":
            if not getattr(args, "file"):
                print("Error: --file argument is required for minify.", file=sys.stderr)
                return False
            with open(args.file, 'r') as f:
                css_text = f.read()
            minified = manager.minify(css_text)

            if getattr(args, "output"):
                with open(args.output, 'w') as f:
                    f.write(minified)
                print(f"Minified CSS written to {args.output}")
            else:
                print(minified)

        elif getattr(args, "action") == "format":
            if not getattr(args, "file"):
                print("Error: --file argument is required for format.", file=sys.stderr)
                return False
            with open(args.file, 'r') as f:
                css_text = f.read()
            formatted = manager.format(css_text)

            if getattr(args, "output"):
                with open(args.output, 'w') as f:
                    f.write(formatted)
                print(f"Formatted CSS written to {args.output}")
            else:
                print(formatted)

        else:
            print("Invalid action or missing required arguments.", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error processing CSS: {e}", file=sys.stderr)
        return False
