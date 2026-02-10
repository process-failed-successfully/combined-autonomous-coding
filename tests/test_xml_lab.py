import unittest
import tempfile
import os
import xml.etree.ElementTree as ET
from shared.xml_lab import XmlLabManager

class TestXmlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = XmlLabManager()
        self.valid_xml = """<root>
    <child id="1">Text1</child>
    <child id="2">Text2</child>
    <nested>
        <subchild>SubText</subchild>
    </nested>
</root>"""
        self.invalid_xml = """<root><child>Missing closing tag</root>"""

    def test_parse_valid(self):
        root = self.manager.parse(self.valid_xml)
        self.assertIsInstance(root, ET.Element)
        self.assertEqual(root.tag, "root")

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.parse(self.invalid_xml)

    def test_load_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(self.valid_xml)
            path = f.name
        try:
            root = self.manager.load_file(path)
            self.assertEqual(root.tag, "root")
        finally:
            os.remove(path)

    def test_validate(self):
        self.assertIsNone(self.manager.validate(self.valid_xml))
        self.assertIsNotNone(self.manager.validate(self.invalid_xml))

    def test_format(self):
        root = self.manager.parse(self.valid_xml)
        formatted = self.manager.format(root)
        self.assertIn("<root>", formatted)
        self.assertIn("  <child", formatted) # Checks indentation

    def test_xpath(self):
        root = self.manager.parse(self.valid_xml)
        results = self.manager.xpath(root, "./child")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].text, "Text1")

        results = self.manager.xpath(root, ".//subchild")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "SubText")

    def test_edit_text(self):
        root = self.manager.parse(self.valid_xml)
        count = self.manager.edit(root, "./child[@id='1']", "NewText")
        self.assertEqual(count, 1)
        self.assertEqual(root.find("./child[@id='1']").text, "NewText")

    def test_edit_attr(self):
        root = self.manager.parse(self.valid_xml)
        count = self.manager.edit(root, "./child[@id='2']", "3", attribute="id")
        self.assertEqual(count, 1)
        self.assertEqual(root.find("./child").attrib.get("id"), "1") # First one unchanged
        # Find the one that was id=2, now id=3.
        # But wait, finding by old id won't work if modified.
        # Find all children
        children = root.findall("./child")
        self.assertEqual(children[1].attrib["id"], "3")

    def test_to_json(self):
        root = self.manager.parse(self.valid_xml)
        data = self.manager.to_json(root)

        # Check structure
        self.assertIn("child", data)
        self.assertIsInstance(data["child"], list)
        self.assertEqual(len(data["child"]), 2)

        # Check text content and attributes
        self.assertEqual(data["child"][0]["#text"], "Text1")
        self.assertEqual(data["child"][0]["@attributes"]["id"], "1")

        # Check nested
        self.assertIn("nested", data)
        self.assertEqual(data["nested"]["subchild"], "SubText")

if __name__ == '__main__':
    unittest.main()
