import sys
import re
from pathlib import Path
from html.parser import HTMLParser


class HtmlToMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.md = []
        self.list_level = 0
        self.list_type = []  # 'ul' or 'ol'
        self.list_counter = []
        self.in_pre = False
        self.in_code = False
        self.in_a = False
        self.a_href = ""
        self.a_text = ""
        self.in_bold = False
        self.in_italic = False
        self.in_blockquote = False

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if re.match(r'^h[1-6]$', tag):
            self.md.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag == 'p':
            self.md.append('\n\n')
        elif tag == 'br':
            self.md.append('\n')
        elif tag == 'hr':
            self.md.append('\n\n---\n\n')
        elif tag in ['ul', 'ol']:
            self.list_level += 1
            self.list_type.append(tag)
            self.list_counter.append(1)
            self.md.append('\n')
        elif tag == 'li':
            indent = '  ' * (self.list_level - 1)
            if self.list_type and self.list_type[-1] == 'ol':
                marker = f"{self.list_counter[-1]}."
                self.list_counter[-1] += 1
            else:
                marker = "-"
            self.md.append(f'\n{indent}{marker} ')
        elif tag in ['b', 'strong']:
            self.md.append('**')
            self.in_bold = True
        elif tag in ['i', 'em']:
            self.md.append('*')
            self.in_italic = True
        elif tag == 'a':
            self.in_a = True
            self.a_href = attr_dict.get('href', '')
            self.a_text = ""
            self.md.append('[')
        elif tag == 'code':
            self.in_code = True
            if not self.in_pre:
                self.md.append('`')
        elif tag == 'pre':
            self.in_pre = True
            self.md.append('\n\n```\n')
        elif tag == 'blockquote':
            self.in_blockquote = True
            self.md.append('\n\n> ')

    def handle_endtag(self, tag):
        if re.match(r'^h[1-6]$', tag) or tag == 'p':
            self.md.append('\n\n')
        elif tag in ['ul', 'ol']:
            self.list_level -= 1
            if self.list_type:
                self.list_type.pop()
                self.list_counter.pop()
            self.md.append('\n')
        elif tag in ['b', 'strong']:
            self.md.append('**')
            self.in_bold = False
        elif tag in ['i', 'em']:
            self.md.append('*')
            self.in_italic = False
        elif tag == 'a':
            self.in_a = False
            self.md.append(f']({self.a_href})')
        elif tag == 'code':
            self.in_code = False
            if not self.in_pre:
                self.md.append('`')
        elif tag == 'pre':
            self.in_pre = False
            self.md.append('\n```\n\n')
        elif tag == 'blockquote':
            self.in_blockquote = False
            self.md.append('\n\n')

    def handle_data(self, data):
        if self.in_pre:
            self.md.append(data)
        else:
            # Clean up whitespace
            cleaned_data = re.sub(r'\s+', ' ', data)
            # If we are inside blockquote, lines should start with >
            if self.in_blockquote:
                cleaned_data = cleaned_data.replace('\n', '\n> ')
            self.md.append(cleaned_data)

    def get_markdown(self):
        result = "".join(self.md)
        # Clean up excessive newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()


class Html2MdManager:
    def convert(self, html: str) -> str:
        parser = HtmlToMarkdownParser()
        parser.feed(html)
        return parser.get_markdown()


def run_html2md_logic(args):
    manager = Html2MdManager()

    html_content = None

    if getattr(args, "file", None):
        try:
            path = Path(args.file)
            html_content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        html_content = args.text
    elif not sys.stdin.isatty():
        html_content = sys.stdin.read()

    if not html_content:
        print("Error: No HTML input provided.", file=sys.stderr)
        return False

    md_output = manager.convert(html_content)

    if getattr(args, "output", None):
        try:
            Path(args.output).write_text(md_output, encoding="utf-8")
            print(f"✅ Markdown saved to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}", file=sys.stderr)
            return False
    else:
        print(md_output)

    return True
