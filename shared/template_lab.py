import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

try:
    import jinja2
    import jinja2.meta
except ImportError:
    jinja2 = None

class TemplateLabManager:
    """
    Manages Jinja2 template operations: render, inspect, lint.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        if not jinja2:
            raise ImportError("jinja2 is required for Template Lab. Please install it with 'pip install Jinja2'.")
        self.project_dir = project_dir or Path(".")
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.project_dir)),
            keep_trailing_newline=True,
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def _load_data(self, data_path: Optional[str]) -> Dict[str, Any]:
        """Loads data from a JSON or YAML file."""
        if not data_path:
            return {}

        path = Path(data_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif path.suffix == '.json':
                    return json.load(f)
                else:
                    # Try JSON then YAML
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return yaml.safe_load(content) or {}
        except Exception as e:
            raise ValueError(f"Error loading data file: {e}")

    def render(self, template_path: str, data_path: Optional[str] = None, overrides: Optional[Dict[str, str]] = None) -> str:
        """
        Renders a template with provided data.
        """
        # We need to handle absolute paths vs relative to project_dir
        # Jinja2 loader is set to project_dir.
        # If template_path is absolute, we might need to adjust loader or path.

        tpl_path = Path(template_path)
        if tpl_path.is_absolute():
            # Create a temporary environment for absolute path
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(tpl_path.parent)),
                keep_trailing_newline=True,
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
            template_name = tpl_path.name
        else:
            # Use project_dir environment
            env = self.env
            template_name = str(tpl_path)

        try:
            template = env.get_template(template_name)
        except jinja2.TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_path}")

        context = self._load_data(data_path)
        if overrides:
            context.update(overrides)

        return template.render(**context)

    def inspect(self, template_path: str) -> Set[str]:
        """
        Finds undeclared variables in the template.
        """
        tpl_path = Path(template_path)
        if tpl_path.is_absolute():
             env = jinja2.Environment(
                 loader=jinja2.FileSystemLoader(str(tpl_path.parent)),
                 autoescape=jinja2.select_autoescape(['html', 'xml'])
             )
             template_source = tpl_path.read_text(encoding='utf-8')
        else:
             # Try resolving relative to project_dir
             full_path = self.project_dir / tpl_path
             if not full_path.exists():
                 raise FileNotFoundError(f"Template not found: {full_path}")
             template_source = full_path.read_text(encoding='utf-8')
             env = self.env

        parsed_content = env.parse(template_source)
        return jinja2.meta.find_undeclared_variables(parsed_content)

    def lint(self, template_path: str) -> Dict[str, Any]:
        """
        Checks for syntax errors in the template.
        """
        tpl_path = Path(template_path)
        if tpl_path.is_absolute():
             env = jinja2.Environment(
                 loader=jinja2.FileSystemLoader(str(tpl_path.parent)),
                 autoescape=jinja2.select_autoescape(['html', 'xml'])
             )
             template_source = tpl_path.read_text(encoding='utf-8')
        else:
             full_path = self.project_dir / tpl_path
             if not full_path.exists():
                 raise FileNotFoundError(f"Template not found: {full_path}")
             template_source = full_path.read_text(encoding='utf-8')
             env = self.env

        try:
            env.parse(template_source)
            return {"valid": True, "message": "Syntax is valid."}
        except jinja2.TemplateSyntaxError as e:
            return {
                "valid": False,
                "message": str(e),
                "line": e.lineno,
                "file": str(template_path)
            }


def run_template_lab_logic(args):
    """CLI logic for Template Lab."""
    try:
        manager = TemplateLabManager(getattr(args, 'project_dir', None))
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "render":
        # Parse overrides from --var key=value
        overrides = {}
        if args.var:
            for v in args.var:
                if '=' in v:
                    key, val = v.split('=', 1)
                    overrides[key] = val

        try:
            result = manager.render(args.template, args.data, overrides)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"✅ Rendered to {args.output}")
            else:
                print(result)
        except Exception as e:
            print(f"❌ Error rendering template: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "inspect":
        try:
            vars_found = manager.inspect(args.template)
            if vars_found:
                print(f"--- Undeclared Variables in {args.template} ---")
                for v in sorted(vars_found):
                    print(f"  - {v}")
            else:
                print(f"✅ No undeclared variables found in {args.template}.")
        except Exception as e:
            print(f"❌ Error inspecting template: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "lint":
        try:
            result = manager.lint(args.template)
            if result["valid"]:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ Syntax Error in {result['file']} at line {result['line']}:")
                print(f"   {result['message']}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error linting template: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
