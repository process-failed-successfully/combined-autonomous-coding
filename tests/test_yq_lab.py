import unittest
from unittest.mock import patch
import sys
import io
import yaml
from shared.yq_lab import YqLabManager, run_yq_lab_logic


class TestYqLab(unittest.TestCase):
    def setUp(self):
        self.manager = YqLabManager()

    def test_evaluate_basic(self):
        yaml_data = """
        name: jules
        age: 30
        hobbies:
          - coding
          - reading
        """
        data = yaml.safe_load(yaml_data)
        result = self.manager.evaluate(data, ".name")
        self.assertEqual(result, "jules")

        result = self.manager.evaluate(data, ".hobbies[0]")
        self.assertEqual(result, "coding")

    def test_evaluate_complex(self):
        yaml_data = """
        users:
          - id: 1
            name: Alice
          - id: 2
            name: Bob
        """
        data = yaml.safe_load(yaml_data)
        result = self.manager.evaluate(data, ".users | map(select(.id == 2)) | .[0].name")
        self.assertEqual(result, "Bob")

    def test_evaluate_invalid_jq(self):
        yaml_data = "name: jules"
        data = yaml.safe_load(yaml_data)
        with self.assertRaises(ValueError):
            self.manager.evaluate(data, ".invalid[syntax]")

    def test_evaluate_empty(self):
        yaml_data = "name: jules"
        data = yaml.safe_load(yaml_data)
        result = self.manager.evaluate(data, "")
        self.assertEqual(result, data)

    def test_evaluate_no_match(self):
        yaml_data = "name: jules"
        data = yaml.safe_load(yaml_data)
        result = self.manager.evaluate(data, ".missing")
        self.assertIsNone(result)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_yq_lab_logic_valid(self, mock_stdout):
        import argparse
        args = argparse.Namespace(
            command="yq-lab",
            action="evaluate",
            input="-",
            expression=".name"
        )

        yaml_input = "name: Bob\n"

        with patch('sys.stdin', io.StringIO(yaml_input)):
            with self.assertRaises(SystemExit) as cm:
                run_yq_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "Bob")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_yq_lab_logic_dump_yaml(self, mock_stdout):
        import argparse
        args = argparse.Namespace(
            command="yq-lab",
            action="evaluate",
            input="-",
            expression=".users"
        )

        yaml_input = "users:\n  - name: Alice\n  - name: Bob"

        with patch('sys.stdin', io.StringIO(yaml_input)):
            with self.assertRaises(SystemExit) as cm:
                run_yq_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue().strip()
        self.assertIn("- name: Alice", output)
        self.assertIn("- name: Bob", output)

if __name__ == '__main__':
    unittest.main()
