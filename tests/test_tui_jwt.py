import unittest
from unittest.mock import MagicMock, patch
import sys

# Define MockContainer before importing module under test
class MockContainer:
    def __init__(self, **kwargs):
        pass

# Mock textual modules
mock_textual = MagicMock()
sys.modules["textual"] = mock_textual
sys.modules["textual.app"] = MagicMock()
sys.modules["textual.containers"] = MagicMock()
# Assign MockContainer to Container in the mocked module
sys.modules["textual.containers"].Container = MockContainer
sys.modules["textual.widgets"] = MagicMock()
sys.modules["textual.reactive"] = MagicMock()
sys.modules["textual.screen"] = MagicMock()
sys.modules["textual.binding"] = MagicMock()

# Now import the module under test
from shared.tui_jwt import JwtLabTab

# We also need to access the widgets to mock isinstance checks or spec
# But since we mocked textual.widgets, we can use those mocks
from textual.widgets import Button, Input, Select, TextArea, RichLog

class TestJwtLabTab(unittest.TestCase):
    def setUp(self):
        self.tab = JwtLabTab()
        self.tab.manager = MagicMock()

        # Mock query_one to return mock widgets
        self.tab.query_one = MagicMock()
        self.mock_text_area = MagicMock()
        self.mock_input = MagicMock()
        self.mock_select = MagicMock()
        self.mock_rich_log = MagicMock()

        def query_one_side_effect(selector, type=None):
            # Check for secrets first or generally check substrings
            if "secret" in selector:
                return self.mock_input
            if "input" in selector:
                return self.mock_text_area
            if "token" in selector:
                # #jwt-verify-token is a TextArea
                return self.mock_text_area
            if "payload" in selector:
                # Payload is a TextArea
                if selector == "#jwt-sign-payload":
                    return self.mock_text_area
                # Decoded payload is RichLog
                if "decode" in selector:
                    return self.mock_rich_log
            if "algo" in selector:
                return self.mock_select
            if "header" in selector or "result" in selector:
                return self.mock_rich_log
            if "output" in selector:
                return self.mock_text_area
            return MagicMock()

        self.tab.query_one.side_effect = query_one_side_effect
        self.tab.notify = MagicMock()

    def test_decode_token(self):
        self.mock_text_area.text = "token.part.three"

        self.tab.manager.decode_token.return_value = {
            "header": {"alg": "HS256"},
            "payload": {"sub": "123"}
        }

        self.tab.decode_token()

        self.tab.manager.decode_token.assert_called_with("token.part.three")
        self.mock_rich_log.write.assert_called()
        self.tab.notify.assert_called_with("Token decoded.")

    def test_sign_token(self):
        self.mock_text_area.text = '{"sub": "123"}' # Payload
        self.mock_input.value = "secret"
        self.mock_select.value = "HS256"
        self.tab.manager.sign_token.return_value = "generated.token"

        self.tab.sign_token()

        self.tab.manager.sign_token.assert_called()
        self.tab.notify.assert_called_with("Token signed.")

    def test_verify_token(self):
        self.mock_text_area.text = "token.part.three"
        self.mock_input.value = "secret"
        self.tab.manager.verify_token.return_value = {
            "header": {"alg": "HS256"},
            "payload": {"sub": "123"}
        }

        self.tab.verify_token()

        self.tab.manager.verify_token.assert_called_with("token.part.three", "secret")
        self.mock_rich_log.write.assert_called()
        self.tab.notify.assert_called_with("Verification successful.")

if __name__ == '__main__':
    unittest.main()
