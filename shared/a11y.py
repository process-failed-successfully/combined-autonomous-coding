import os
import re
import fnmatch
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Dict, Set, Tuple, Optional

class A11yViolation:
    def __init__(self, rule_id: str, message: str, file: str, lineno: int, severity: str = "ERROR"):
        self.rule_id = rule_id
        self.message = message
        self.file = file
        self.lineno = lineno
        self.severity = severity

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "file": self.file,
            "lineno": self.lineno,
            "severity": self.severity
        }

class HTMLScanner(HTMLParser):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.violations: List[A11yViolation] = []
        self.current_line = 1
        self.ids: Set[str] = set()
        self.headings: List[Tuple[int, int]] = [] # (level, lineno)
        self.stack: List[Dict] = [] # {tag, lineno, has_content, attrs}

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        lineno, _ = self.getpos()
        attr_dict = {k: v for k, v in attrs if k is not None}

        self.stack.append({
            "tag": tag,
            "lineno": lineno,
            "has_content": False,
            "attrs": attr_dict
        })

        # Check: img missing alt
        if tag == "img":
            if "alt" not in attr_dict:
                self.violations.append(A11yViolation(
                    "img-alt-missing",
                    "<img> element missing 'alt' attribute.",
                    self.file_path,
                    lineno
                ))
            elif not attr_dict["alt"].strip():
                # Empty alt is valid for decorative images, but worth a warning if not marked role="presentation"
                if attr_dict.get("role") != "presentation" and attr_dict.get("aria-hidden") != "true":
                     self.violations.append(A11yViolation(
                        "img-alt-empty",
                        "<img> has empty 'alt' attribute. Ensure it is decorative or add description.",
                        self.file_path,
                        lineno,
                        severity="WARNING"
                    ))

        # Check: html missing lang
        if tag == "html":
            if "lang" not in attr_dict:
                self.violations.append(A11yViolation(
                    "html-lang-missing",
                    "<html> element missing 'lang' attribute.",
                    self.file_path,
                    lineno
                ))

        # Check: a invalid href
        if tag == "a":
            href = attr_dict.get("href")
            if not href or href == "#" or href.startswith("javascript:"):
                 self.violations.append(A11yViolation(
                    "a-href-invalid",
                    "<a> element has invalid or missing 'href' attribute.",
                    self.file_path,
                    lineno,
                    severity="WARNING"
                ))

        # Track headings
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            try:
                level = int(tag[1])
                self.headings.append((level, lineno))
            except ValueError:
                pass

        # Track IDs
        if "id" in attr_dict:
            self.ids.add(attr_dict["id"])

    def handle_endtag(self, tag):
        # Pop from stack until we find the tag
        while self.stack:
            item = self.stack.pop()
            if item["tag"] == tag:
                self.check_element_on_close(item)
                break

    def handle_data(self, data):
        if not self.stack: return
        if data.strip():
            self.stack[-1]["has_content"] = True

    def check_element_on_close(self, item):
        tag = item["tag"]
        attrs = item["attrs"]
        lineno = item["lineno"]
        has_content = item["has_content"]

        if tag == "button":
             has_label = "aria-label" in attrs or "aria-labelledby" in attrs or "title" in attrs
             if not has_content and not has_label:
                 self.violations.append(A11yViolation(
                    "button-empty",
                    "<button> is empty and has no accessible label.",
                    self.file_path,
                    lineno
                ))

    def validate_structure(self):
        # Check heading hierarchy
        if not self.headings:
            return

        # Check if it starts with h1 (optional but recommended)
        # if self.headings[0][0] != 1:
        #     self.violations.append(A11yViolation(
        #         "heading-order",
        #         "Page structure should ideally start with an <h1>.",
        #         self.file_path,
        #         self.headings[0][1],
        #         severity="INFO"
        #     ))

        for i in range(len(self.headings) - 1):
            current, lineno = self.headings[i]
            next_level, next_lineno = self.headings[i+1]
            if next_level > current + 1:
                self.violations.append(A11yViolation(
                    "heading-jump",
                    f"Skipped heading level: <h{current}> to <h{next_level}>.",
                    self.file_path,
                    next_lineno,
                    severity="WARNING"
                ))

class AccessibilityScanner:
    def __init__(self, project_dir: Path, file_pattern: str = None, ignore_patterns: List[str] = None):
        self.project_dir = project_dir
        self.file_pattern = file_pattern
        self.ignore_patterns = ignore_patterns or []
        self.violations: List[A11yViolation] = []

    def is_ignored(self, file_path: Path) -> bool:
        rel_path = str(file_path.relative_to(self.project_dir))
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if pattern.endswith("/") and rel_path.startswith(pattern):
                return True
        return False

    def scan(self):
        extensions = [".html", ".htm", ".jsx", ".tsx", ".vue"]
        if self.file_pattern:
            # If user specified pattern, trust it
             for root, dirs, files in os.walk(self.project_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]
                for file in files:
                    if fnmatch.fnmatch(file, self.file_pattern):
                         self.scan_file(Path(root) / file)
        else:
            # Auto-detect web files
            for root, dirs, files in os.walk(self.project_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in extensions:
                         self.scan_file(Path(root) / file)

    def scan_file(self, file_path: Path):
        if self.is_ignored(file_path):
            return

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            ext = file_path.suffix.lower()

            if ext in [".html", ".htm"]:
                self.scan_html(file_path, content)
            else:
                self.scan_regex(file_path, content)
        except Exception as e:
            # print(f"Error scanning {file_path}: {e}")
            pass

    def scan_html(self, file_path: Path, content: str):
        parser = HTMLScanner(str(file_path.relative_to(self.project_dir)))
        parser.feed(content)
        parser.validate_structure()
        self.violations.extend(parser.violations)

    def scan_regex(self, file_path: Path, content: str):
        rel_path = str(file_path.relative_to(self.project_dir))
        lines = content.splitlines()

        # Regex patterns for JSX/Vue
        # These are heuristic and not perfect
        img_pattern = re.compile(r"<img\s+[^>]*>")
        alt_pattern = re.compile(r"alt=['\"{]")

        for i, line in enumerate(lines):
            lineno = i + 1

            # Check img
            for match in img_pattern.finditer(line):
                tag = match.group(0)
                if not alt_pattern.search(tag):
                    self.violations.append(A11yViolation(
                        "img-alt-missing",
                        "<img> missing 'alt' prop.",
                        rel_path,
                        lineno
                    ))

            # Check for click handlers on non-interactive elements (div/span)
            # onClick with no role="button" or key events
            if "onClick=" in line or "@click" in line:
                if "<div" in line or "<span" in line:
                    if "role=" not in line:
                        self.violations.append(A11yViolation(
                            "click-no-role",
                            "Click handler on <div>/<span> without role='button'.",
                            rel_path,
                            lineno,
                            severity="WARNING"
                        ))

            # Check for generic "Button" text
            # Very naive check
            if "<button>" in line and "</button>" in line:
                text = line.split("<button>")[1].split("</button>")[0].strip()
                if not text:
                     self.violations.append(A11yViolation(
                        "button-empty",
                        "<button> is empty.",
                        rel_path,
                        lineno
                    ))
                elif text.lower() in ["click here", "read more"]:
                     self.violations.append(A11yViolation(
                        "link-text-quality",
                        f"Avoid generic link text like '{text}'.",
                        rel_path,
                        lineno,
                        severity="INFO"
                    ))

def _run_a11y_logic(project_dir: Path, files: str = None, ignore: str = None, output_format: str = "text"):
    ignore_patterns = [p.strip() for p in ignore.split(",")] if ignore else []

    # Default ignores
    if not ignore:
        ignore_patterns = [".git*", "node_modules*", "dist*", "build*", ".next*"]

    print(f"--- Accessibility Scanner in: {project_dir} ---")

    scanner = AccessibilityScanner(project_dir, files, ignore_patterns)
    scanner.scan()

    if not scanner.violations:
        print("✅ No accessibility violations found.")
        return

    # Sort violations
    scanner.violations.sort(key=lambda x: (x.severity != "ERROR", x.file, x.lineno))

    if output_format == "json":
        import json
        print(json.dumps([v.to_dict() for v in scanner.violations], indent=2))
        return

    # Console output
    current_file = None
    count = 0
    for v in scanner.violations:
        count += 1
        if v.file != current_file:
            print(f"\n📄 {v.file}")
            current_file = v.file

        # Color code severity
        sev_display = v.severity
        if v.severity == "ERROR":
            sev_display = f"\033[91m{v.severity}\033[0m"
        elif v.severity == "WARNING":
            sev_display = f"\033[93m{v.severity}\033[0m"
        elif v.severity == "INFO":
            sev_display = f"\033[94m{v.severity}\033[0m"

        print(f"  Line {v.lineno:<4} [{sev_display}] {v.message}")

    print(f"\nFound {count} issue(s).")

    # Exit with code 1 if errors found
    if any(v.severity == "ERROR" for v in scanner.violations):
        import sys
        sys.exit(1)
