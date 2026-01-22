import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
from shared.link_checker import LinkChecker


class TestLinkChecker(unittest.TestCase):
    def test_extract_links(self) -> None:
        checker = LinkChecker()
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tf:
            tf.write("Check out https://google.com and http://example.org.\n")
            tf.write("Also see (https://github.com).\n")
            tf.write("Ignore: https://internal.dev")
            tf_path = Path(tf.name)

        try:
            checker.ignore_patterns = ["internal.dev"]
            links = checker.extract_links_from_file(tf_path)

            # Expected: google.com, example.org, github.com. internal.dev is ignored.
            urls = [u for _, u in links]
            self.assertIn("https://google.com", urls)
            self.assertIn("http://example.org", urls)
            self.assertIn("https://github.com", urls)
            self.assertNotIn("https://internal.dev", urls)

        finally:
            if tf_path.exists():
                os.unlink(tf_path)

    @patch('shared.link_checker.requests.head')
    @patch('shared.link_checker.requests.get')
    def test_check_url_ok(self, mock_get: MagicMock, mock_head: MagicMock) -> None:
        checker = LinkChecker()

        # Test 200 OK via HEAD
        mock_head.return_value.status_code = 200
        mock_head.return_value.ok = True

        res = checker.check_url("https://example.com")
        self.assertTrue(res['ok'])
        self.assertEqual(res['status'], 200)

        # Test 405 Method Not Allowed via HEAD -> GET 200
        mock_head.return_value.status_code = 405
        mock_get.return_value.status_code = 200
        mock_get.return_value.ok = True

        res = checker.check_url("https://example.org")
        self.assertTrue(res['ok'])
        self.assertEqual(res['status'], 200)

    @patch('shared.link_checker.requests.head')
    def test_check_url_fail(self, mock_head: MagicMock) -> None:
        checker = LinkChecker()
        mock_head.return_value.status_code = 404
        mock_head.return_value.ok = False

        res = checker.check_url("https://broken.com")
        self.assertFalse(res['ok'])
        self.assertEqual(res['status'], 404)

    def test_check_url_with_session(self) -> None:
        checker = LinkChecker()
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_session.head.return_value = mock_response

        res = checker.check_url("https://example.com", session=mock_session)

        # Verify session.head was called
        mock_session.head.assert_called_once()
        self.assertTrue(res['ok'])
        self.assertEqual(res['status'], 200)
