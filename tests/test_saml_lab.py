import unittest
import base64
import zlib
import argparse
from unittest.mock import patch
from shared.saml_lab import SamlLabManager, run_saml_lab_logic

class TestSamlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SamlLabManager()
        self.sample_xml = "<saml:Assertion xmlns:saml=\"urn:oasis:names:tc:SAML:2.0:assertion\"><saml:Issuer>test</saml:Issuer></saml:Assertion>"

    def test_decode_plain_base64(self):
        encoded = base64.b64encode(self.sample_xml.encode('utf-8')).decode('utf-8')
        result = self.manager.decode(encoded, inflate=False)
        self.assertIn("saml:Assertion", result)
        self.assertIn("saml:Issuer", result)

    def test_decode_deflated(self):
        # Deflate without zlib header
        compress_obj = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
        compressed = compress_obj.compress(self.sample_xml.encode('utf-8')) + compress_obj.flush()

        encoded = base64.b64encode(compressed).decode('utf-8')
        result = self.manager.decode(encoded, inflate=True)
        self.assertIn("saml:Assertion", result)

    def test_decode_deflated_with_header(self):
        # Deflate with zlib header
        compressed = zlib.compress(self.sample_xml.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        result = self.manager.decode(encoded, inflate=True)
        self.assertIn("saml:Assertion", result)

    def test_decode_url_encoded(self):
        encoded = base64.b64encode(self.sample_xml.encode('utf-8')).decode('utf-8')
        # URL encode the base64 string
        import urllib.parse
        url_encoded = urllib.parse.quote(encoded)
        result = self.manager.decode(url_encoded, inflate=False)
        self.assertIn("saml:Assertion", result)

    def test_decode_invalid_base64(self):
        with self.assertRaises(ValueError):
            self.manager.decode("!@#$%^", inflate=False)

    def test_decode_empty(self):
        with self.assertRaises(ValueError):
            self.manager.decode("")

class TestSamlLabCLI(unittest.TestCase):
    @patch('builtins.print')
    def test_cli_decode(self, mock_print):
        sample_xml = "<test>hello</test>"
        encoded = base64.b64encode(sample_xml.encode('utf-8')).decode('utf-8')
        args = argparse.Namespace(decode=encoded, file=None, inflate=False)
        try:
            run_saml_lab_logic(args)
        except SystemExit:
            pass
        mock_print.assert_called()
        # the output is pretty printed XML, so it might span multiple calls or one large string
        # Let's check the arguments passed to print
        called_with_xml = False
        for call_args in mock_print.call_args_list:
            if "hello" in call_args[0][0]:
                called_with_xml = True
        self.assertTrue(called_with_xml)

if __name__ == '__main__':
    unittest.main()
