import argparse
import sys
from defusedxml.ElementTree import parse as defused_parse
import re
from pathlib import Path

class SvgLabManager:
    def __init__(self):
        pass

    def validate(self, filepath: Path) -> bool:
        """Validates if a file is a well-formed SVG."""
        if not filepath.exists():
            print(f"❌ Error: File not found: {filepath}", file=sys.stderr)
            return False

        try:
            tree = defused_parse(filepath)
            root = tree.getroot()
            # Basic check for SVG tag
            tag = root.tag
            # Tag could have a namespace like {http://www.w3.org/2000/svg}svg
            # It should end with 'svg'
            tag_name = tag.split('}')[-1] if '}' in tag else tag
            if tag_name.lower() == "svg":
                print(f"✅ SVG is valid and well-formed: {filepath}")
                return True
            else:
                print(f"❌ Document does not appear to be an SVG (root tag: {tag})", file=sys.stderr)
                return False
        except ET.ParseError as e:
            print(f"❌ Invalid SVG/XML format in {filepath}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error validating SVG: {e}", file=sys.stderr)
            return False

    def minify(self, filepath: Path, output_path: Path = None) -> bool:
        """Minifies an SVG file by removing unnecessary whitespace and comments."""
        if not filepath.exists():
            print(f"❌ Error: File not found: {filepath}", file=sys.stderr)
            return False

        try:
            content = filepath.read_text(encoding="utf-8")
            original_size = len(content)

            # Basic minification steps using regex (without requiring external libs)
            # Remove comments
            minified = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            # Remove newlines, tabs, and multiple spaces
            minified = re.sub(r'>\s+<', '><', minified)
            minified = re.sub(r'\s{2,}', ' ', minified)
            minified = minified.strip()

            new_size = len(minified)

            out_path = output_path if output_path else filepath

            out_path.write_text(minified, encoding="utf-8")

            savings = original_size - new_size
            pct = (savings / original_size * 100) if original_size > 0 else 0

            print(f"✅ Minified SVG saved to {out_path}")
            print(f"   Original size: {original_size} bytes")
            print(f"   New size:      {new_size} bytes")
            print(f"   Reduced by:    {savings} bytes ({pct:.1f}%)")
            return True
        except Exception as e:
            print(f"❌ Error minifying SVG: {e}", file=sys.stderr)
            return False


def run_svg_lab_logic(args: argparse.Namespace) -> bool:
    """Entry point for SVG Lab."""
    manager = SvgLabManager()

    if args.action == "validate":
        if not args.file:
            print("❌ Error: --file is required for validate action.", file=sys.stderr)
            return False
        return manager.validate(Path(args.file))

    elif args.action == "minify":
        if not args.file:
            print("❌ Error: --file is required for minify action.", file=sys.stderr)
            return False
        out_path = Path(args.output) if getattr(args, "output", None) else None
        return manager.minify(Path(args.file), out_path)

    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        return False
