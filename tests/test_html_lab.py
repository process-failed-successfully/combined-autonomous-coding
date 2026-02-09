import unittest
from shared.html_lab import HTMLLabManager

class TestHTMLLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HTMLLabManager()

    def test_extract_tag_text(self):
        html = "<html><body><h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p></body></html>"
        results = self.manager.extract(html, tag="p")
        self.assertEqual(results, ["Paragraph 1", "Paragraph 2"])

    def test_extract_nested_text(self):
        html = "<div>Outer <span>Inner</span></div>"
        # HTMLExtractor should extract recursive text
        results = self.manager.extract(html, tag="div")
        self.assertEqual(results, ["Outer Inner"])

    def test_extract_attr(self):
        html = '<a href="http://example.com">Link</a><a href="http://test.com">Test</a>'
        results = self.manager.extract(html, tag="a", attr="href")
        self.assertEqual(results, ["http://example.com", "http://test.com"])

    def test_extract_by_id(self):
        html = '<div id="one">One</div><div id="two">Two</div>'
        results = self.manager.extract(html, tag="div", id="two")
        self.assertEqual(results, ["Two"])

    def test_extract_by_class(self):
        html = '<div class="foo">Foo</div><div class="bar">Bar</div><div class="foo bar">FooBar</div>'
        results = self.manager.extract(html, tag="div", class_name="foo")
        self.assertEqual(results, ["Foo", "FooBar"])

    def test_clean_strip_all(self):
        html = "<p>Hello <b>World</b></p>"
        result = self.manager.clean(html)
        self.assertEqual(result, "Hello World")

    def test_clean_keep_tags(self):
        html = "<p>Hello <b>World</b></p>"
        result = self.manager.clean(html, tags_to_keep=["b"])
        self.assertEqual(result, "Hello <b>World</b>")

    def test_table_parsing(self):
        html = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td>30</td></tr>
            <tr><td>Bob</td><td>25</td></tr>
        </table>
        """
        rows = self.manager.table(html)
        expected = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"]
        ]
        self.assertEqual(rows, expected)

    def test_table_nested(self):
        html = """
        <table>
            <tr><td>Outer</td><td>
                <table>
                    <tr><td>Inner</td></tr>
                </table>
            </td></tr>
        </table>
        """
        rows = self.manager.table(html)
        # Should ignore nested table content when parsing the outer table
        expected = [["Outer", ""]]
        self.assertEqual(rows, expected)

    def test_validate_valid(self):
        html = "<div><p>Valid</p></div>"
        errors = self.manager.validate(html)
        self.assertEqual(errors, [])

    def test_validate_invalid(self):
        html = "<div><p>Invalid</div>"
        errors = self.manager.validate(html)
        self.assertTrue(len(errors) > 0)
        self.assertIn("Mismatched closing tag", errors[0])

if __name__ == '__main__':
    unittest.main()
