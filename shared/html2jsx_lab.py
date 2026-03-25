import sys
import re
from html.parser import HTMLParser

class HtmlToJsxParser(HTMLParser):
    def __init__(self, create_component=False, component_name="MyComponent"):
        super().__init__()
        self.result = []
        self.create_component = create_component
        self.component_name = component_name
        self.self_closing_tags = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }
        self.in_script_or_style = False

    def _camel_case(self, s: str) -> str:
        parts = s.split('-')
        if len(parts) == 1:
            return s
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])

    def _parse_style(self, style_str: str) -> str:
        styles = []
        for prop in style_str.split(';'):
            prop = prop.strip()
            if not prop:
                continue
            if ':' not in prop:
                continue
            key, val = prop.split(':', 1)
            key = key.strip()
            val = val.strip()
            camel_key = self._camel_case(key)
            val = val.replace("'", "\\'")
            styles.append(f"{camel_key}: '{val}'")
        return "{{" + ", ".join(styles) + "}}"

    def handle_starttag(self, tag, attrs):
        self._handle_tag(tag, attrs, is_startend=False)

    def handle_startendtag(self, tag, attrs):
        self._handle_tag(tag, attrs, is_startend=True)

    def _handle_tag(self, tag, attrs, is_startend):
        props = []
        for k, v in attrs:
            # React specific replacements
            if k == 'class':
                k = 'className'
            elif k == 'for':
                k = 'htmlFor'
            elif '-' in k and not k.startswith('data-') and not k.startswith('aria-'):
                k = self._camel_case(k)
            elif k == 'tabindex':
                k = 'tabIndex'
            elif k == 'readonly':
                k = 'readOnly'
            elif k == 'maxlength':
                k = 'maxLength'
            elif k == 'autofocus':
                k = 'autoFocus'
            elif k == 'autocomplete':
                k = 'autoComplete'
            elif k == 'colspan':
                k = 'colSpan'
            elif k == 'rowspan':
                k = 'rowSpan'

            if k == 'style' and v:
                v_jsx = self._parse_style(v)
                props.append(f"{k}={v_jsx}")
            else:
                if v is None:
                    # Boolean attribute
                    props.append(f"{k}")
                else:
                    # Normal attribute
                    # Escape quotes in string
                    v = v.replace('"', '&quot;')
                    props.append(f'{k}="{v}"')

        props_str = " " + " ".join(props) if props else ""

        if tag in self.self_closing_tags or is_startend:
            self.result.append(f"<{tag}{props_str} />")
        else:
            self.result.append(f"<{tag}{props_str}>")
            if tag.lower() in ('script', 'style'):
                self.in_script_or_style = True

    def handle_endtag(self, tag):
        if tag.lower() in ('script', 'style'):
            self.in_script_or_style = False
        if tag not in self.self_closing_tags:
            self.result.append(f"</{tag}>")

    def handle_data(self, data):
        # Escape curly braces in text content for JSX, but do not escape if inside script tags
        if not self.in_script_or_style:
            data = data.replace('{', '&#123;').replace('}', '&#125;')
        self.result.append(data)

    def handle_entityref(self, name):
        self.result.append(f"&{name};")

    def handle_charref(self, name):
        self.result.append(f"&#{name};")

    def handle_comment(self, data):
        self.result.append(f"{{/* {data} */}}")

    def get_jsx(self):
        content = "".join(self.result)
        if self.create_component:
            return f"export default function {self.component_name}() {{\n  return (\n    <>\n      {content}\n    </>\n  );\n}}"
        return content

class Html2JsxManager:
    def convert(self, html_str: str, create_component: bool = False, component_name: str = "MyComponent") -> str:
        if not html_str or not html_str.strip():
            return ""

        parser = HtmlToJsxParser(create_component=create_component, component_name=component_name)
        try:
            parser.feed(html_str)
            return parser.get_jsx()
        except Exception as e:
            return f"Error parsing HTML: {e}"

def run_html2jsx_lab_logic(args) -> bool:
    """CLI logic for HTML to JSX Lab."""
    manager = Html2JsxManager()

    content = None
    if getattr(args, "file", None):
        import pathlib
        path = pathlib.Path(args.file)
        if not path.exists():
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            return False
        content = path.read_text(encoding="utf-8", errors="replace")
    elif getattr(args, "text", None):
        content = args.text
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: Input required via --file, --text, or stdin.", file=sys.stderr)
            return False

    create_component = getattr(args, "component", False)
    component_name = getattr(args, "name", "MyComponent")

    jsx = manager.convert(content, create_component, component_name)

    if getattr(args, "output", None):
        import pathlib
        path = pathlib.Path(args.output)
        path.write_text(jsx, encoding="utf-8")
        print(f"✅ Saved JSX to {args.output}")
    else:
        print(jsx)

    return True
