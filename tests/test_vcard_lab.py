import unittest
import sys
from pathlib import Path
import tempfile
import shutil

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.vcard_lab import VCardManager

class TestVCardLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = VCardManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_vcard_basic(self):
        details = {
            "fn": "John Doe",
            "n": "Doe;John;;;",
            "email": "john@example.com"
        }
        vcard = self.manager.generate_vcard(details)
        self.assertIn("BEGIN:VCARD", vcard)
        self.assertIn("VERSION:3.0", vcard)
        self.assertIn("FN:John Doe", vcard)
        self.assertIn("N:Doe;John;;;", vcard)
        self.assertIn("EMAIL;TYPE=INTERNET:john@example.com", vcard)
        self.assertIn("END:VCARD", vcard)

    def test_generate_vcard_multiple_lists(self):
        details = {
            "fn": "Jane Doe",
            "email": ["jane1@example.com", "jane2@example.com"],
            "tel": ["555-1234", "555-5678"],
            "url": ["https://example.com", "https://jane.example.com"]
        }
        vcard = self.manager.generate_vcard(details)
        self.assertIn("EMAIL;TYPE=INTERNET:jane1@example.com", vcard)
        self.assertIn("EMAIL;TYPE=INTERNET:jane2@example.com", vcard)
        self.assertIn("TEL;TYPE=VOICE,CELL:555-1234", vcard)
        self.assertIn("TEL;TYPE=VOICE,CELL:555-5678", vcard)
        self.assertIn("URL:https://example.com", vcard)
        self.assertIn("URL:https://jane.example.com", vcard)

    def test_generate_vcard_escaping(self):
        details = {
            "note": "Line 1\nLine 2"
        }
        vcard = self.manager.generate_vcard(details)
        self.assertIn("NOTE:Line 1\\nLine 2", vcard)

    def test_parse_vcard_basic(self):
        content = """BEGIN:VCARD
VERSION:3.0
FN:Alice Smith
ORG:Acme Corp
EMAIL;TYPE=INTERNET:alice@example.com
END:VCARD
"""
        vcards = self.manager.parse_vcard(content)
        self.assertEqual(len(vcards), 1)
        self.assertEqual(vcards[0]["fn"], "Alice Smith")
        self.assertEqual(vcards[0]["org"], "Acme Corp")
        self.assertEqual(vcards[0]["email"], ["alice@example.com"])

    def test_parse_vcard_multiple(self):
        content = """BEGIN:VCARD
FN:User One
END:VCARD
BEGIN:VCARD
FN:User Two
TEL;TYPE=VOICE:123
TEL;TYPE=CELL:456
NOTE:Line 1\\nLine 2
ADR:;;123 Main St;City;State;12345;Country
END:VCARD"""
        vcards = self.manager.parse_vcard(content)
        self.assertEqual(len(vcards), 2)
        self.assertEqual(vcards[0]["fn"], "User One")
        self.assertEqual(vcards[1]["fn"], "User Two")
        self.assertEqual(vcards[1]["tel"], ["123", "456"])
        self.assertEqual(vcards[1]["note"], "Line 1\nLine 2")
        self.assertIn("123 Main St, City, State, 12345, Country", vcards[1]["adr"])
