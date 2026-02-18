import unittest
from unittest.mock import MagicMock, patch
from shared.tui_jwt import JwtLabTab

class TestJwtLabTab(unittest.TestCase):
    def setUp(self):
        self.tab = JwtLabTab()
        # Mock query_one
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()

    @patch("shared.tui_jwt.JWTManager")
    def test_decode_success(self, MockJWTManager):
        # Setup mocks
        mock_input = MagicMock()
        mock_input.text = "token123"

        mock_header_log = MagicMock()
        mock_payload_log = MagicMock()

        def query_side_effect(selector, *args):
            if selector == "#jwt-decode-input": return mock_input
            if selector == "#jwt-decode-header": return mock_header_log
            if selector == "#jwt-decode-payload": return mock_payload_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        MockJWTManager.decode_token.return_value = {
            "header": {"alg": "HS256"},
            "payload": {"sub": "123"}
        }

        # Action
        self.tab.on_decode()

        # Verify
        MockJWTManager.decode_token.assert_called_with("token123")
        mock_header_log.clear.assert_called()
        mock_payload_log.clear.assert_called()
        # Should write Syntax object
        self.assertTrue(mock_header_log.write.called)
        self.assertTrue(mock_payload_log.write.called)

    @patch("shared.tui_jwt.JWTManager")
    def test_sign_success(self, MockJWTManager):
        # Setup mocks
        mock_payload_area = MagicMock()
        mock_payload_area.text = '{"sub": "123"}'

        mock_secret_input = MagicMock()
        mock_secret_input.value = "secret"

        mock_algo_select = MagicMock()
        mock_algo_select.value = "HS256"

        mock_output_area = MagicMock()

        def query_side_effect(selector, *args):
            if selector == "#jwt-sign-payload": return mock_payload_area
            if selector == "#jwt-sign-secret": return mock_secret_input
            if selector == "#jwt-sign-algo": return mock_algo_select
            if selector == "#jwt-sign-output": return mock_output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        MockJWTManager.sign_token.return_value = "signed_token"

        # Action
        self.tab.on_sign()

        # Verify
        MockJWTManager.sign_token.assert_called_with({"sub": "123"}, "secret", algo="HS256")
        self.assertEqual(mock_output_area.text, "signed_token")
        self.tab.notify.assert_called_with("Token generated.")

    @patch("shared.tui_jwt.JWTManager")
    def test_verify_success(self, MockJWTManager):
        # Setup mocks
        mock_token_area = MagicMock()
        mock_token_area.text = "token123"

        mock_secret_input = MagicMock()
        mock_secret_input.value = "secret"

        mock_result_log = MagicMock()

        def query_side_effect(selector, *args):
            if selector == "#jwt-verify-token": return mock_token_area
            if selector == "#jwt-verify-secret": return mock_secret_input
            if selector == "#jwt-verify-result": return mock_result_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        MockJWTManager.decode_token.return_value = {"payload": {}}

        # Action
        self.tab.on_verify()

        # Verify
        MockJWTManager.verify_token.assert_called_with("token123", "secret")
        self.assertTrue(mock_result_log.write.called)

    @patch("shared.tui_jwt.JWTManager")
    def test_verify_fail(self, MockJWTManager):
        # Setup mocks
        mock_token_area = MagicMock()
        mock_token_area.text = "token123"

        mock_secret_input = MagicMock()
        mock_secret_input.value = "wrong_secret"

        mock_result_log = MagicMock()

        def query_side_effect(selector, *args):
            if selector == "#jwt-verify-token": return mock_token_area
            if selector == "#jwt-verify-secret": return mock_secret_input
            if selector == "#jwt-verify-result": return mock_result_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        MockJWTManager.verify_token.side_effect = ValueError("Invalid signature")

        # Action
        self.tab.on_verify()

        # Verify
        MockJWTManager.verify_token.assert_called_with("token123", "wrong_secret")
        # Check that error was written to log
        args, _ = mock_result_log.write.call_args
        self.assertIn("Verification Failed", args[0])

if __name__ == '__main__':
    unittest.main()
