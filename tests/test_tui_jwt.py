import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Ensure shared module is available (just in case)
sys.path.append(str(Path(__file__).parent.parent))

# Handle Textual dependency: use real if available (CI), mock if not (Local)
try:
    import textual
    from textual.widgets import TextArea, Input, Select, RichLog
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    # Create Mocks for sys.modules to satisfy imports in shared.tui_jwt
    mock_textual = MagicMock()
    sys.modules["textual"] = mock_textual

    mock_app = MagicMock()
    sys.modules["textual.app"] = mock_app

    mock_containers = MagicMock()
    # Container must be a class because it is inherited from
    mock_containers.Container = MagicMock
    mock_containers.Horizontal = MagicMock
    mock_containers.Vertical = MagicMock
    sys.modules["textual.containers"] = mock_containers

    mock_widgets = MagicMock()

    # Button must support Button.Pressed for type hinting
    # If we make Button a MagicMock instance, Button.Pressed works.
    # If we make it a class, we need to ensure Pressed is on it.
    mock_button = MagicMock()
    mock_button.Pressed = MagicMock() # Ensure Pressed exists
    mock_widgets.Button = mock_button

    mock_widgets.Input = MagicMock()
    mock_widgets.Label = MagicMock()
    mock_widgets.RichLog = MagicMock()
    mock_widgets.Select = MagicMock()
    mock_widgets.TabbedContent = MagicMock()
    mock_widgets.TabPane = MagicMock()
    mock_widgets.TextArea = MagicMock()
    sys.modules["textual.widgets"] = mock_widgets

    # We need to mock textual.work to just return the function itself for tests
    def dummy_work(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    mock_textual.work = dummy_work

    # Assign local aliases for use in tests
    TextArea = mock_widgets.TextArea
    Input = mock_widgets.Input
    Select = mock_widgets.Select
    RichLog = mock_widgets.RichLog

import pytest

if TEXTUAL_AVAILABLE:
    # Use real Textual Work decorator override for tests
    # MUST be done before importing JwtLabTab
    def dummy_work(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    textual.work = dummy_work

from shared.tui_jwt import JwtLabTab

# We want to run this test regardless, but mock the worker
class TestJwtLabTab(unittest.TestCase):
    def setUp(self):
        # Patch JWTManager to avoid real crypto and verify logic isolation
        with patch('shared.tui_jwt.JWTManager') as MockManager:
            self.tab = JwtLabTab()
            # self.tab.manager is now the mock instance
            self.mock_manager = self.tab.manager

        # Mock query_one to return our mock widgets
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()

        # Create mock widgets
        self.mock_text_area = MagicMock()
        self.mock_input = MagicMock()
        self.mock_select = MagicMock()
        self.mock_rich_log = MagicMock()

        def query_one_side_effect(selector, type=None):
            # Selector logic to return appropriate mock
            if "secret" in selector or "wordlist" in selector:
                return self.mock_input

            if "algo" in selector:
                return self.mock_select

            if "header" in selector or "result" in selector:
                return self.mock_rich_log

            # Disambiguate 'payload'
            if "payload" in selector:
                # #jwt-decode-payload is RichLog
                # #jwt-sign-payload is TextArea
                if "decode" in selector:
                    return self.mock_rich_log
                else:
                    return self.mock_text_area

            # TextAreas (input, token, output)
            if "input" in selector or "token" in selector or "output" in selector:
                return self.mock_text_area

            return MagicMock()

        self.tab.query_one.side_effect = query_one_side_effect

    def test_decode_token(self):
        # Setup inputs
        self.mock_text_area.text = "token.part.three"

        # Setup manager return
        self.mock_manager.decode_token.return_value = {
            "header": {"alg": "HS256"},
            "payload": {"sub": "123"}
        }

        # Execute
        self.tab.decode_token()

        # Verify
        self.mock_manager.decode_token.assert_called_with("token.part.three")
        self.mock_rich_log.write.assert_called()
        self.tab.notify.assert_called_with("Token decoded.")

    def test_sign_token(self):
        # Setup inputs
        self.mock_text_area.text = '{"sub": "123"}' # Payload text
        self.mock_input.value = "secret"
        self.mock_select.value = "HS256"

        self.mock_manager.sign_token.return_value = "generated.token"

        # Execute
        self.tab.sign_token()

        # Verify
        self.mock_manager.sign_token.assert_called()
        # The output TextArea (.text) should be set to the token
        self.assertEqual(self.mock_text_area.text, "generated.token")
        self.tab.notify.assert_called_with("Token signed.")

    def test_verify_token(self):
        # Setup inputs
        self.mock_text_area.text = "token.part.three"
        self.mock_input.value = "secret"

        self.mock_manager.verify_token.return_value = {
            "header": {"alg": "HS256"},
            "payload": {"sub": "123"}
        }

        # Execute
        self.tab.verify_token()

        # Verify
        self.mock_manager.verify_token.assert_called_with("token.part.three", "secret")
        self.mock_rich_log.write.assert_called()
        self.tab.notify.assert_called_with("Verification successful.")

    def test_crack_token(self):
        # Setup inputs
        self.mock_text_area.text = "token.part.three"
        self.mock_input.value = "wordlist.txt"

        self.mock_manager.crack_token.return_value = "cracked_secret"

        # Execute
        # Since it uses @work which calls the worker method, we can bypass the Textual
        # dispatch and just call crack_token_worker directly to test the core logic
        # that communicates with the manager. Or test them separately.
        # However, for simple coverage, we can just call the worker synchronously here.
        # But wait, crack_token_worker calls self.app.call_from_thread, which we also need to mock.

        mock_app = MagicMock()
        def call_from_thread_mock(func, *args, **kwargs):
             func(*args, **kwargs)
        mock_app.call_from_thread = call_from_thread_mock

        # Mock self.app explicitly
        type(self.tab).app = mock_app

        self.tab.crack_token_worker("token.part.three", "wordlist.txt")

        # Verify
        self.mock_manager.crack_token.assert_called_with("token.part.three", "wordlist.txt")
        self.mock_rich_log.write.assert_called()
        self.tab.notify.assert_called_with("Token cracked successfully.")

if __name__ == '__main__':
    unittest.main()
