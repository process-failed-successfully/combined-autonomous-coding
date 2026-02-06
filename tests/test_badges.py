import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.badges import BadgeGenerator, run_badges_logic
import argparse

class TestBadgeGenerator(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.generator = BadgeGenerator(self.project_dir)

    def test_estimate_width(self):
        width = self.generator._estimate_width("Tests")
        self.assertIsInstance(width, int)
        self.assertGreater(width, 0)

    def test_estimate_width_variable(self):
        # "iii" should be narrower than "MMM" even with same length
        width_i = self.generator._estimate_width("iii")
        width_m = self.generator._estimate_width("MMM")
        self.assertLess(width_i, width_m)

    def test_generate_badge(self):
        svg = self.generator.generate_badge("Tests", "Passing", "#4c1")
        self.assertIn('<svg', svg)
        self.assertIn('Tests', svg)
        self.assertIn('Passing', svg)
        self.assertIn('#4c1', svg)

    @patch('pathlib.Path.exists')
    def test_get_test_status_passing(self, mock_exists):
        mock_exists.return_value = True
        status = self.generator.get_test_status()
        self.assertEqual(status['value'], 'passing')
        self.assertEqual(status['color'], '#4c1')

    @patch('pathlib.Path.exists')
    def test_get_test_status_unknown(self, mock_exists):
        mock_exists.return_value = False
        status = self.generator.get_test_status()
        self.assertEqual(status['value'], 'unknown')
        self.assertEqual(status['color'], '#9f9f9f')

    @patch('shared.badges.SecurityAuditor')
    def test_get_security_count(self, MockAuditor):
        # Mock instance
        mock_instance = MockAuditor.return_value
        # Mock scan_secrets return value (list of findings)
        mock_instance.scan_secrets.return_value = [{"type": "secret"}] # 1 finding

        status = self.generator.get_security_count()
        self.assertEqual(status['value'], '1 issues')
        self.assertEqual(status['color'], '#e05d44')

        # Test zero issues
        mock_instance.scan_secrets.return_value = []
        status = self.generator.get_security_count()
        self.assertEqual(status['value'], '0 issues')
        self.assertEqual(status['color'], '#4c1')

    @patch('shared.badges.scan_todos')
    def test_get_todo_count(self, mock_scan):
        mock_scan.return_value = ["todo1", "todo2"]
        status = self.generator.get_todo_count()
        self.assertEqual(status['value'], '2 pending')

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_update_readme_insert(self, mock_exists, mock_write, mock_read):
        mock_exists.return_value = True
        mock_read.return_value = "# My Project\nDescription."

        badges = {"Tests": "<svg>...</svg>"}
        self.generator.update_readme(badges)

        # Check if write was called with inserted block
        args, _ = mock_write.call_args
        content = args[0]
        self.assertIn("<!-- BADGES_START -->", content)
        self.assertIn("![Tests](./badge_tests.svg)", content)
        self.assertIn("<!-- BADGES_END -->", content)
        self.assertIn("# My Project", content)

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.exists')
    def test_update_readme_replace(self, mock_exists, mock_write, mock_read):
        mock_exists.return_value = True
        mock_read.return_value = """# My Project
<!-- BADGES_START -->
old content
<!-- BADGES_END -->
Description."""

        badges = {"Tests": "<svg>...</svg>"}
        self.generator.update_readme(badges)

        args, _ = mock_write.call_args
        content = args[0]
        self.assertIn("![Tests](./badge_tests.svg)", content)
        self.assertNotIn("old content", content)

class TestRunBadgesLogic(unittest.TestCase):
    @patch('shared.badges.BadgeGenerator')
    def test_create_action(self, MockGenerator):
        args = argparse.Namespace(
            action="create",
            project_dir=Path("."),
            label="Label",
            value="Value",
            color="red",
            output="out.svg"
        )

        # Mock generate_badge
        mock_gen = MockGenerator.return_value
        mock_gen.generate_badge.return_value = "<svg></svg>"

        with patch('pathlib.Path.write_text') as mock_write:
            run_badges_logic(args)
            mock_write.assert_called_with("<svg></svg>", encoding="utf-8")

    @patch('shared.badges.BadgeGenerator')
    def test_generate_action(self, MockGenerator):
        args = argparse.Namespace(
            action="generate",
            project_dir=Path("."),
            update_readme=True
        )

        mock_gen = MockGenerator.return_value
        # Mock metric returns
        mock_gen.get_test_status.return_value = {"value": "v", "color": "c"}
        mock_gen.get_security_count.return_value = {"value": "v", "color": "c"}
        mock_gen.get_todo_count.return_value = {"value": "v", "color": "c"}
        mock_gen.generate_badge.return_value = "<svg></svg>"

        run_badges_logic(args)

        # Ensure update_readme was called
        mock_gen.update_readme.assert_called()

if __name__ == '__main__':
    unittest.main()
