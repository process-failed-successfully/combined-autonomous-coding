import unittest
import sys
import io
import argparse
from shared.http_status_lab import HttpStatusLabManager, run_http_status_lab_logic


class TestHttpStatusLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HttpStatusLabManager()

    def test_get_status_valid(self):
        res = self.manager.get_status(200)
        self.assertIsNotNone(res)
        self.assertEqual(res["code"], 200)
        self.assertEqual(res["message"], "OK")
        self.assertEqual(res["category"], "2xx Success")

    def test_get_status_invalid(self):
        res = self.manager.get_status(999)
        self.assertIsNone(res)

    def test_search_status_by_code(self):
        res = self.manager.search_status("404")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["code"], 404)

    def test_search_status_by_text(self):
        res = self.manager.search_status("teapot")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["code"], 418)

    def test_search_status_no_match(self):
        res = self.manager.search_status("unobtainium")
        self.assertEqual(len(res), 0)


class TestHttpStatusLabCLI(unittest.TestCase):
    def setUp(self):
        # Redirect stdout and stderr
        self.held_out = io.StringIO()
        self.held_err = io.StringIO()
        self.original_out = sys.stdout
        self.original_err = sys.stderr
        sys.stdout = self.held_out
        sys.stderr = self.held_err

    def tearDown(self):
        sys.stdout = self.original_out
        sys.stderr = self.original_err

    def test_cli_get_valid(self):
        args = argparse.Namespace(action="get", query="418")
        result = run_http_status_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("I'm a teapot", self.held_out.getvalue())

    def test_cli_get_invalid_code(self):
        args = argparse.Namespace(action="get", query="999")
        result = run_http_status_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("not found", self.held_err.getvalue())

    def test_cli_get_non_numeric(self):
        args = argparse.Namespace(action="get", query="abc")
        result = run_http_status_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("requires a numeric", self.held_err.getvalue())

    def test_cli_search_match(self):
        args = argparse.Namespace(action="search", query="not found")
        result = run_http_status_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("[404] Not Found", self.held_out.getvalue())

    def test_cli_search_no_match(self):
        args = argparse.Namespace(action="search", query="xyzxyz")
        result = run_http_status_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("No HTTP status codes found", self.held_out.getvalue())

    def test_cli_search_missing_query(self):
        args = argparse.Namespace(action="search", query="")
        result = run_http_status_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Search query required", self.held_err.getvalue())


if __name__ == "__main__":
    unittest.main()
