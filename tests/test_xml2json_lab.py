import unittest
import json
from unittest.mock import patch, mock_open, MagicMock
from argparse import Namespace
from pathlib import Path

from shared.xml2json_lab import Xml2JsonManager, run_xml2json_lab_logic

class TestXml2JsonManager(unittest.TestCase):
    def setUp(self):
        self.manager = Xml2JsonManager()

    def test_convert_empty(self):
        self.assertEqual(self.manager.convert(""), "{}")
        self.assertEqual(self.manager.convert("   "), "{}")
        self.assertEqual(self.manager.convert(None), "{}")

    def test_convert_simple(self):
        xml = "<root>hello</root>"
        expected = {"root": "hello"}
        result = json.loads(self.manager.convert(xml))
        self.assertEqual(result, expected)

    def test_convert_attributes(self):
        xml = "<root id='1' name='test'>hello</root>"
        expected = {"root": {"@id": "1", "@name": "test", "#text": "hello"}}
        result = json.loads(self.manager.convert(xml))
        self.assertEqual(result, expected)

    def test_convert_nested(self):
        xml = "<root><child>value</child></root>"
        expected = {"root": {"child": "value"}}
        result = json.loads(self.manager.convert(xml))
        self.assertEqual(result, expected)

    def test_convert_list(self):
        xml = "<root><item>1</item><item>2</item></root>"
        expected = {"root": {"item": ["1", "2"]}}
        result = json.loads(self.manager.convert(xml))
        self.assertEqual(result, expected)

    def test_convert_complex(self):
        xml = """
        <catalog>
            <book id="bk101">
                <author>Gambardella, Matthew</author>
                <title>XML Developer's Guide</title>
            </book>
            <book id="bk102">
                <author>Ralls, Kim</author>
                <title>Midnight Rain</title>
            </book>
        </catalog>
        """
        expected = {
            "catalog": {
                "book": [
                    {
                        "@id": "bk101",
                        "author": "Gambardella, Matthew",
                        "title": "XML Developer's Guide"
                    },
                    {
                        "@id": "bk102",
                        "author": "Ralls, Kim",
                        "title": "Midnight Rain"
                    }
                ]
            }
        }
        result = json.loads(self.manager.convert(xml))
        self.assertEqual(result, expected)

    def test_convert_invalid_xml(self):
        with self.assertRaises(ValueError):
            self.manager.convert("<root>unclosed")


class TestRunXml2JsonLabLogic(unittest.TestCase):
    @patch('shared.xml2json_lab.sys.stdout')
    def test_run_logic_with_text(self, mock_stdout):
        args = Namespace(text="<root>test</root>", file=None, output=None)
        self.assertTrue(run_xml2json_lab_logic(args))
        # Ensure it printed out the json string containing root: test
        printed_str = mock_stdout.write.call_args_list[0][0][0]
        self.assertIn('"root": "test"', printed_str)

    @patch('shared.xml2json_lab.Path.is_file', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="<root>test file</root>")
    @patch('shared.xml2json_lab.sys.stdout')
    def test_run_logic_with_file(self, mock_stdout, mock_file, mock_is_file):
        args = Namespace(text=None, file="input.xml", output=None)
        self.assertTrue(run_xml2json_lab_logic(args))
        printed_str = mock_stdout.write.call_args_list[0][0][0]
        self.assertIn('"root": "test file"', printed_str)

    @patch('shared.xml2json_lab.Path.is_file', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data="<root>test file</root>")
    @patch('shared.xml2json_lab.Path.write_text')
    def test_run_logic_with_output(self, mock_write_text, mock_file, mock_is_file):
        args = Namespace(text=None, file="input.xml", output="out.json")
        self.assertTrue(run_xml2json_lab_logic(args))
        mock_write_text.assert_called_once()
        written_str = mock_write_text.call_args[0][0]
        self.assertIn('"root": "test file"', written_str)

    @patch('shared.xml2json_lab.sys.stderr')
    def test_run_logic_invalid_args(self, mock_stderr):
        args = Namespace(text=None, file=None, output=None)
        self.assertFalse(run_xml2json_lab_logic(args))
        mock_stderr.write.assert_called()

    @patch('shared.xml2json_lab.sys.stderr')
    def test_run_logic_invalid_xml(self, mock_stderr):
        args = Namespace(text="<root>unclosed", file=None, output=None)
        self.assertFalse(run_xml2json_lab_logic(args))
        mock_stderr.write.assert_called()

if __name__ == '__main__':
    unittest.main()
