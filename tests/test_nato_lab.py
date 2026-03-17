import unittest
from unittest.mock import patch
import io
import argparse
from shared.nato_lab import NatoLabManager, run_nato_lab_logic

class TestNatoLab(unittest.TestCase):
    def setUp(self):
        self.manager = NatoLabManager()

    def test_encode_basic(self):
        self.assertEqual(self.manager.encode("SOS"), "Sierra Oscar Sierra")
        self.assertEqual(self.manager.encode("cat"), "Charlie Alfa Tango")

    def test_encode_with_spaces(self):
        self.assertEqual(self.manager.encode("a b"), "Alfa  Bravo")
        self.assertEqual(self.manager.encode("Hello World"), "Hotel Echo Lima Lima Oscar  Whiskey Oscar Romeo Lima Delta")

    def test_encode_with_punctuation(self):
        self.assertEqual(self.manager.encode("Hi!"), "Hotel India !")
        self.assertEqual(self.manager.encode("A1"), "Alfa One")
        self.assertEqual(self.manager.encode("test-1"), "Tango Echo Sierra Tango - One")

    def test_decode_basic(self):
        self.assertEqual(self.manager.decode("Sierra Oscar Sierra"), "SOS")
        self.assertEqual(self.manager.decode("Charlie Alfa Tango"), "CAT")

    def test_decode_case_insensitive(self):
        self.assertEqual(self.manager.decode("sierra OSCAR SiErRa"), "SOS")
        self.assertEqual(self.manager.decode("alfa"), "A")
        self.assertEqual(self.manager.decode("alpha"), "A") # alias testing

    def test_decode_with_spaces(self):
        self.assertEqual(self.manager.decode("Alfa  Bravo"), "A B")
        self.assertEqual(self.manager.decode("Hotel Echo Lima Lima Oscar  Whiskey Oscar Romeo Lima Delta"), "HELLO WORLD")

    def test_decode_with_punctuation(self):
        self.assertEqual(self.manager.decode("Hotel India !"), "HI!")
        self.assertEqual(self.manager.decode("Alfa One"), "A1")
        self.assertEqual(self.manager.decode("Tango Echo Sierra Tango - One"), "TEST-1")

    def test_decode_unmapped_words(self):
        self.assertEqual(self.manager.decode("Hotel Hello Oscar"), "HHelloO")
        self.assertEqual(self.manager.decode("RandomWord"), "RandomWord")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(encode="abc", decode=None, tui=False)
        result = run_nato_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("Alfa Bravo Charlie", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="Alfa Bravo Charlie", tui=False)
        result = run_nato_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("ABC", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_nato_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
