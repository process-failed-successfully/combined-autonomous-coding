import unittest
from pathlib import Path
import tempfile
import shutil
from shared.a11y import AccessibilityScanner


class TestAccessibilityScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content):
        path = self.test_dir / filename
        path.write_text(content, encoding='utf-8')
        return path

    def test_html_scanner_valid(self):
        content = """
        <!DOCTYPE html>
        <html lang="en">
        <head><title>Test</title></head>
        <body>
            <h1>Heading 1</h1>
            <img src="img.jpg" alt="Description">
            <button aria-label="Close"></button>
            <a href="/link">Link</a>
        </body>
        </html>
        """
        self.create_file("valid.html", content)
        scanner = AccessibilityScanner(self.test_dir)
        scanner.scan()
        self.assertEqual(len(scanner.violations), 0)

    def test_html_scanner_violations(self):
        content = """
        <!DOCTYPE html>
        <html>
        <body>
            <h3>Skipped Heading</h3>
            <img src="img.jpg">
            <button></button>
            <a href="#">Invalid Link</a>
        </body>
        </html>
        """
        self.create_file("invalid.html", content)
        scanner = AccessibilityScanner(self.test_dir)
        scanner.scan()

        violations = scanner.violations
        self.assertTrue(len(violations) >= 4)

        rule_ids = [v.rule_id for v in violations]
        self.assertIn("html-lang-missing", rule_ids)
        # self.assertIn("heading-jump", rule_ids) # h1 -> h3 is jump? default parser starts at 1. if h3 is first, it might not trigger jump from prev.
        # Wait, my logic checks for jump between headings. If h3 is first, it's not a jump from previous.
        # But let's check img-alt-missing
        self.assertIn("img-alt-missing", rule_ids)
        self.assertIn("a-href-invalid", rule_ids)

    def test_heading_jump(self):
        content = """
        <!DOCTYPE html>
        <html lang="en">
        <body>
            <h1>Heading 1</h1>
            <h3>Heading 3</h3>
        </body>
        </html>
        """
        self.create_file("jump.html", content)
        scanner = AccessibilityScanner(self.test_dir)
        scanner.scan()

        violations = scanner.violations
        rule_ids = [v.rule_id for v in violations]
        self.assertIn("heading-jump", rule_ids)

    def test_jsx_regex_scanner(self):
        content = """
        import React from 'react';

        export const Component = () => {
            return (
                <div>
                    <img src="img.jpg" />
                    <div onClick={() => {}}>Click Me</div>
                    <button>Click here</button>
                </div>
            );
        };
        """
        self.create_file("component.jsx", content)
        scanner = AccessibilityScanner(self.test_dir)
        scanner.scan()

        violations = scanner.violations
        rule_ids = [v.rule_id for v in violations]

        self.assertIn("img-alt-missing", rule_ids)
        self.assertIn("click-no-role", rule_ids)
        self.assertIn("link-text-quality", rule_ids)

    def test_ignore_patterns(self):
        content = '<img src="img.jpg">'
        self.create_file("ignore_me.html", content)

        scanner = AccessibilityScanner(self.test_dir, ignore_patterns=["ignore_me.html"])
        scanner.scan()

        self.assertEqual(len(scanner.violations), 0)

    def test_file_pattern(self):
        self.create_file("test.html", '<img src="a.jpg">')
        self.create_file("test.txt", 'ignore')

        scanner = AccessibilityScanner(self.test_dir, file_pattern="*.html")
        scanner.scan()

        # Should scan html but text scanner wouldn't find violations anyway unless forced.
        # But we check if scan_file was called.
        # Checking violations count: test.html has 1 violation (missing lang, missing alt)
        self.assertTrue(len(scanner.violations) > 0)


if __name__ == '__main__':
    unittest.main()
