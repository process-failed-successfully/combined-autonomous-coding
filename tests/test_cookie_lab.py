import unittest
import argparse
from unittest.mock import patch
from shared.cookie_lab import CookieLabManager, run_cookie_lab_logic

class TestCookieLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CookieLabManager()

    def test_parse_simple_cookie(self):
        cookie_string = "session_id=12345"
        result = self.manager.parse(cookie_string)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "session_id")
        self.assertEqual(result[0]["value"], "12345")

    def test_parse_complex_cookie(self):
        cookie_string = "session_id=12345; Secure; HttpOnly; SameSite=Strict; Domain=example.com; Path=/; Max-Age=3600"
        result = self.manager.parse(cookie_string)
        self.assertEqual(len(result), 1)
        c = result[0]
        self.assertEqual(c["name"], "session_id")
        self.assertEqual(c["value"], "12345")
        self.assertTrue(c["secure"])
        self.assertTrue(c["httponly"])
        self.assertEqual(c["samesite"], "Strict")
        self.assertEqual(c["domain"], "example.com")
        self.assertEqual(c["path"], "/")
        self.assertEqual(c["max-age"], "3600")

    def test_parse_multiple_cookies(self):
        cookie_string = "session_id=12345; user=abc"
        result = self.manager.parse(cookie_string)
        self.assertEqual(len(result), 2)

        # http.cookies.SimpleCookie dictionary keys aren't strictly ordered, but typically they are parsed in order
        cookies = {c["name"]: c for c in result}
        self.assertIn("session_id", cookies)
        self.assertIn("user", cookies)
        self.assertEqual(cookies["session_id"]["value"], "12345")
        self.assertEqual(cookies["user"]["value"], "abc")

    def test_generate_simple_cookie(self):
        result = self.manager.generate("session_id", "12345")
        self.assertEqual(result, "Set-Cookie: session_id=12345")

    def test_generate_complex_cookie(self):
        result = self.manager.generate(
            "session_id",
            "12345",
            secure=True,
            httponly=True,
            samesite="Strict",
            domain="example.com",
            path="/",
            max_age="3600"
        )
        # The exact order of attributes isn't guaranteed by SimpleCookie,
        # but we can check if they are all present.
        self.assertTrue(result.startswith("Set-Cookie: session_id=12345; "))
        self.assertIn("Secure", result)
        self.assertIn("HttpOnly", result)
        self.assertIn("SameSite=Strict", result)
        self.assertIn("Domain=example.com", result)
        self.assertIn("Path=/", result)
        self.assertIn("Max-Age=3600", result)

class TestCookieLabCLI(unittest.TestCase):
    @patch('sys.stdout')
    def test_cli_parse(self, mock_stdout):
        args = argparse.Namespace(
            action="parse",
            cookie_string="test=123",
            tui=False
        )
        run_cookie_lab_logic(args)

    @patch('sys.stdout')
    def test_cli_generate(self, mock_stdout):
        args = argparse.Namespace(
            action="generate",
            name="test",
            value="123",
            tui=False
        )
        run_cookie_lab_logic(args)

if __name__ == "__main__":
    unittest.main()
