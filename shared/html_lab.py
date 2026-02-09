import sys
import json
import csv
from html.parser import HTMLParser
from typing import List, Optional, Any

class HTMLExtractor(HTMLParser):
    def __init__(self, tag: Optional[str] = None, attr: Optional[str] = None, id: Optional[str] = None, class_name: Optional[str] = None):
        super().__init__()
        self.tag = tag
        self.attr = attr
        self.id = id
        self.class_name = class_name
        self.results: List[str] = []
        self._capture = False
        self._depth = 0
        self._match_tag = None
        self._current_data: List[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if not self._capture:
            match = True
            if self.tag and tag != self.tag: match = False
            if self.id and attrs_dict.get('id') != self.id: match = False
            if self.class_name:
                classes = attrs_dict.get('class', '').split()
                if self.class_name not in classes: match = False

            if match:
                if self.attr:
                    val = attrs_dict.get(self.attr)
                    if val: self.results.append(val)
                else:
                    self._capture = True
                    self._match_tag = tag
                    self._depth = 1
                    self._current_data = []
        else:
            if tag == self._match_tag:
                self._depth += 1

    def handle_endtag(self, tag):
        if self._capture:
            if tag == self._match_tag:
                self._depth -= 1
                if self._depth == 0:
                    # Capture complete
                    self.results.append("".join(self._current_data).strip())
                    self._capture = False
                    self._match_tag = None

    def handle_data(self, data):
        if self._capture:
            self._current_data.append(data)

class HTMLCleaner(HTMLParser):
    def __init__(self, tags_to_keep: Optional[List[str]] = None):
        super().__init__()
        self.tags_to_keep = set(tags_to_keep) if tags_to_keep else set()
        self.results: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.tags_to_keep:
            attr_str = "".join(f' {k}="{v}"' for k, v in attrs)
            self.results.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag):
        if tag in self.tags_to_keep:
            self.results.append(f"</{tag}>")

    def handle_data(self, data):
        self.results.append(data)

class HTMLTableParser(HTMLParser):
    def __init__(self, table_index: int = 0):
        super().__init__()
        self.table_index = table_index
        self.current_table_index = -1
        self.in_target_table = False
        self.in_row = False
        self.in_cell = False
        self.rows: List[List[str]] = []
        self.current_row: List[str] = []
        self.current_cell_data: List[str] = []
        self.nested_tables = 0 # Track nested tables to avoid confusion

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if not self.in_target_table:
                self.current_table_index += 1
                if self.current_table_index == self.table_index:
                    self.in_target_table = True
            else:
                self.nested_tables += 1

        if self.in_target_table and self.nested_tables == 0:
            if tag == 'tr':
                self.in_row = True
                self.current_row = []
            elif tag in ('td', 'th'):
                self.in_cell = True
                self.current_cell_data = []

    def handle_endtag(self, tag):
        if tag == 'table':
            if self.in_target_table:
                if self.nested_tables > 0:
                    self.nested_tables -= 1
                else:
                    self.in_target_table = False

        if self.in_target_table and self.nested_tables == 0:
            if tag == 'tr':
                self.in_row = False
                if self.current_row:
                    self.rows.append(self.current_row)
            elif tag in ('td', 'th'):
                self.in_cell = False
                self.current_row.append("".join(self.current_cell_data).strip())

    def handle_data(self, data):
        if self.in_cell and self.nested_tables == 0:
            self.current_cell_data.append(data)

class HTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: List[str] = []
        self.errors: List[str] = []
        # Void elements that don't need closing tags
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag not in self.void_elements:
            if not self.stack:
                self.errors.append(f"Unexpected closing tag: </{tag}>")
            elif self.stack[-1] == tag:
                self.stack.pop()
            else:
                self.errors.append(f"Mismatched closing tag: </{tag}>. Expected </{self.stack[-1]}>")

    def validate(self) -> List[str]:
        if self.stack:
            for tag in reversed(self.stack):
                self.errors.append(f"Unclosed tag: <{tag}>")
        return self.errors

class HTMLLabManager:
    def extract(self, html_content: str, tag: str = None, attr: str = None, id: str = None, class_name: str = None) -> List[str]:
        parser = HTMLExtractor(tag, attr, id, class_name)
        parser.feed(html_content)
        return parser.results

    def clean(self, html_content: str, tags_to_keep: List[str] = None) -> str:
        parser = HTMLCleaner(tags_to_keep)
        parser.feed(html_content)
        return "".join(parser.results)

    def table(self, html_content: str, table_index: int = 0) -> List[List[str]]:
        parser = HTMLTableParser(table_index)
        parser.feed(html_content)
        return parser.rows

    def validate(self, html_content: str) -> List[str]:
        parser = HTMLValidator()
        parser.feed(html_content)
        return parser.validate()

def run_html_lab_logic(args):
    manager = HTMLLabManager()

    # Read input
    content = ""
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        if not sys.stdin.isatty():
             content = sys.stdin.read()
        else:
             print("Error: Input file or stdin required.", file=sys.stderr)
             sys.exit(1)

    if args.action == "extract":
        results = manager.extract(content, args.tag, args.attr, args.id, args.class_name)
        for r in results:
            print(r)

    elif args.action == "clean":
        tags = args.keep.split(",") if args.keep else None
        print(manager.clean(content, tags))

    elif args.action == "table":
        rows = manager.table(content, args.index)
        if args.format == "csv":
            writer = csv.writer(sys.stdout)
            writer.writerows(rows)
        elif args.format == "json":
            print(json.dumps(rows, indent=2))

    elif args.action == "validate":
        errors = manager.validate(content)
        if errors:
            print(f"❌ Found {len(errors)} validation errors:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print("✅ HTML structure seems valid (basic check).")
            sys.exit(0)

    sys.exit(0)
