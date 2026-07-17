#!/bin/bash
sed -i 's/[ \t]*$//' shared/saml_lab.py
sed -i 's/[ \t]*$//' tests/test_saml_lab.py
sed -i 's/[ \t]*$//' tests/test_tui_saml.py

cat << 'INNER_EOF' > tests/test_tui_saml.py
import unittest
import base64
from unittest.mock import MagicMock
from shared.tui_saml import SamlLabTab
from textual.app import App
from textual.widgets import TextArea, Checkbox


class DummyApp(App):
    def compose(self):
        yield SamlLabTab()

    async def on_mount(self):
        self.notify = MagicMock()


class TestSamlLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_decode_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            sample_xml = "<samlp:AuthnRequest xmlns:samlp=\"urn:oasis:names:tc:SAML:2.0:protocol\"><saml:Issuer xmlns:saml=\"urn:oasis:names:tc:SAML:2.0:assertion\">TestIssuer</saml:Issuer></samlp:AuthnRequest>"
            encoded = base64.b64encode(sample_xml.encode('utf-8')).decode('utf-8')

            # Set values
            app.query_one("#saml-input", TextArea).text = encoded
            app.query_one("#saml-inflate-chk", Checkbox).value = False

            # Click decode
            await pilot.click("#btn-saml-decode")

            # Verify result
            result_text = app.query_one("#saml-result", TextArea).text
            self.assertIn("TestIssuer", result_text)
            self.assertIn("samlp:AuthnRequest", result_text)

    async def test_decode_with_saml_request_prefix(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            sample_xml = "<test>data</test>"
            encoded = base64.b64encode(sample_xml.encode('utf-8')).decode('utf-8')

            app.query_one("#saml-input", TextArea).text = f"SAMLRequest={encoded}"
            app.query_one("#saml-inflate-chk", Checkbox).value = False

            await pilot.click("#btn-saml-decode")

            result_text = app.query_one("#saml-result", TextArea).text
            self.assertIn("data", result_text)
            self.assertIn("<test>", result_text)


if __name__ == '__main__':
    unittest.main()
INNER_EOF
