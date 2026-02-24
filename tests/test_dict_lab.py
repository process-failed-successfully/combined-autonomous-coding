import unittest
from unittest.mock import MagicMock, patch
import sys
import io
from shared.dict_lab import DictLabManager, run_dict_lab_logic

class TestDictLab(unittest.TestCase):

    def setUp(self):
        self.manager = DictLabManager()
        self.sample_response = [
            {
                "word": "hello",
                "phonetic": "həˈləʊ",
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {
                                "definition": "Greeting.",
                                "synonyms": ["greeting", "salutation"],
                                "antonyms": []
                            }
                        ],
                        "synonyms": ["hi"],
                        "antonyms": ["goodbye"]
                    }
                ]
            }
        ]

    @patch('shared.dict_lab.requests.get')
    def test_lookup_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.sample_response
        mock_get.return_value = mock_resp

        result = self.manager.lookup("hello")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], self.sample_response)

    @patch('shared.dict_lab.requests.get')
    def test_lookup_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = self.manager.lookup("asdfghjkl")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    def test_get_definitions(self):
        defs = self.manager.get_definitions(self.sample_response)
        self.assertEqual(len(defs), 1)
        self.assertEqual(defs[0]["definition"], "Greeting.")
        self.assertEqual(defs[0]["part_of_speech"], "noun")

    def test_get_synonyms(self):
        synonyms = self.manager.get_synonyms(self.sample_response)
        expected = sorted(["greeting", "salutation", "hi"])
        self.assertEqual(synonyms, expected)

    def test_get_antonyms(self):
        antonyms = self.manager.get_antonyms(self.sample_response)
        expected = ["goodbye"]
        self.assertEqual(antonyms, expected)

    @patch('shared.dict_lab.requests.get')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_define(self, mock_stdout, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.sample_response
        mock_get.return_value = mock_resp

        args = MagicMock()
        args.word = "hello"
        args.action = "define"

        try:
            run_dict_lab_logic(args)
        except SystemExit:
            pass

        output = mock_stdout.getvalue()
        self.assertIn("Definitions for: hello", output)
        self.assertIn("Greeting.", output)

if __name__ == '__main__':
    unittest.main()
