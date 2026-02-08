import unittest
from io import StringIO
from unittest.mock import patch, MagicMock
from shared.semver_lab import SemVer, run_semver_lab_logic

class TestSemVer(unittest.TestCase):
    def test_parse_valid(self):
        v = SemVer("1.2.3")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertIsNone(v.prerelease)
        self.assertIsNone(v.buildmetadata)

        v = SemVer("1.2.3-alpha.1+build.123")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertEqual(v.prerelease, "alpha.1")
        self.assertEqual(v.buildmetadata, "build.123")

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            SemVer("1.2")
        with self.assertRaises(ValueError):
            SemVer("v1.2.3") # Regex expects strict semver (no v prefix)
        with self.assertRaises(ValueError):
            SemVer("1.2.3.4")

    def test_str(self):
        self.assertEqual(str(SemVer("1.2.3")), "1.2.3")
        self.assertEqual(str(SemVer("1.0.0-beta")), "1.0.0-beta")
        self.assertEqual(str(SemVer("2.0.0+exp.sha.5114f85")), "2.0.0+exp.sha.5114f85")

    def test_bump(self):
        v = SemVer("1.2.3")
        self.assertEqual(str(v.bump("major")), "2.0.0")
        self.assertEqual(str(v.bump("minor")), "1.3.0")
        self.assertEqual(str(v.bump("patch")), "1.2.4")

        # Test prerelease bumps
        v_pre = SemVer("1.2.3-alpha.0")
        self.assertEqual(str(v_pre.bump("patch")), "1.2.3") # prerelease -> release
        self.assertEqual(str(v_pre.bump("prerelease")), "1.2.3-alpha.1") # increment

        v_stable = SemVer("1.2.3")
        self.assertEqual(str(v_stable.bump("prerelease", pre_id="beta.0")), "1.2.4-beta.0")

    def test_compare(self):
        self.assertTrue(SemVer("1.0.0") < SemVer("2.0.0"))
        self.assertTrue(SemVer("2.0.0") > SemVer("1.0.0"))
        self.assertTrue(SemVer("1.2.0") < SemVer("1.3.0"))
        self.assertTrue(SemVer("1.2.3") < SemVer("1.2.4"))

        # Prerelease precedence
        self.assertTrue(SemVer("1.0.0-alpha") < SemVer("1.0.0"))
        self.assertTrue(SemVer("1.0.0-alpha") < SemVer("1.0.0-alpha.1"))
        self.assertTrue(SemVer("1.0.0-alpha.1") < SemVer("1.0.0-alpha.beta"))
        self.assertTrue(SemVer("1.0.0-beta") < SemVer("1.0.0-beta.2"))
        self.assertTrue(SemVer("1.0.0-beta.2") < SemVer("1.0.0-beta.11")) # Numeric comparison
        self.assertTrue(SemVer("1.0.0-alpha") < SemVer("1.0.0-beta"))

        self.assertEqual(SemVer("1.2.3"), SemVer("1.2.3"))

        # Build metadata should be ignored in comparison
        self.assertEqual(SemVer("1.2.3+build1"), SemVer("1.2.3+build2"))

    def test_sort(self):
        versions = [
            SemVer("1.0.0"),
            SemVer("1.0.0-alpha"),
            SemVer("1.0.0-beta"),
            SemVer("0.9.0")
        ]
        sorted_versions = sorted(versions)
        expected = ["0.9.0", "1.0.0-alpha", "1.0.0-beta", "1.0.0"]
        self.assertEqual([str(v) for v in sorted_versions], expected)

class TestRunSemVerLabLogic(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_parse_cmd(self, mock_stdout):
        args = MagicMock()
        args.action = "parse"
        args.version = "1.2.3-alpha"

        with self.assertRaises(SystemExit) as cm:
            run_semver_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Major:          1", output)
        self.assertIn("Prerelease:     alpha", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_bump_cmd(self, mock_stdout):
        args = MagicMock()
        args.action = "bump"
        args.version = "1.2.3"
        args.part = "minor"
        args.pre_id = None

        with self.assertRaises(SystemExit) as cm:
            run_semver_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "1.3.0")

    @patch('sys.stdout', new_callable=StringIO)
    def test_compare_cmd(self, mock_stdout):
        args = MagicMock()
        args.action = "compare"
        args.version1 = "1.0.0"
        args.version2 = "2.0.0"

        with self.assertRaises(SystemExit) as cm:
            run_semver_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_stdout.getvalue().strip(), "1.0.0 < 2.0.0")

    @patch('sys.stdout', new_callable=StringIO)
    def test_sort_cmd(self, mock_stdout):
        args = MagicMock()
        args.action = "sort"
        args.versions = ["1.0.0", "0.1.0", "2.0.0"]
        args.reverse = False

        with self.assertRaises(SystemExit) as cm:
            run_semver_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue().splitlines()
        self.assertEqual(output, ["0.1.0", "1.0.0", "2.0.0"])

    @patch('sys.stdout', new_callable=StringIO)
    def test_validate_cmd(self, mock_stdout):
        args = MagicMock()
        args.action = "validate"
        args.version = "1.2.3"

        with self.assertRaises(SystemExit) as cm:
            run_semver_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Valid SemVer", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
