import unittest
import os
import json
import yaml  # type: ignore
from tempfile import NamedTemporaryFile
from shared.yaml2json_lab import Yaml2JsonManager, run_yaml2json_lab_logic


class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestYaml2JsonManager(unittest.TestCase):
    def setUp(self):
        self.manager = Yaml2JsonManager()

    def test_convert_yaml_to_json_string(self):
        yaml_str = "key: value\nlist:\n  - 1\n  - 2"
        expected = json.dumps({"key": "value", "list": [1, 2]}, indent=2)
        result = self.manager.convert_yaml_to_json(yaml_str)
        self.assertEqual(result, expected)

    def test_convert_yaml_to_json_file(self):
        yaml_str = "key: value\nlist:\n  - 1\n  - 2"
        expected = json.dumps({"key": "value", "list": [1, 2]}, indent=2)

        with NamedTemporaryFile(mode='w', delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_str)
            tmp_path = tmp.name

        try:
            result = self.manager.convert_yaml_to_json(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_convert_yaml_to_json_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.convert_yaml_to_json(":")

    def test_convert_json_to_yaml_string(self):
        json_str = '{"key": "value", "list": [1, 2]}'
        expected = yaml.dump({"key": "value", "list": [1, 2]}, sort_keys=False, default_flow_style=False)
        result = self.manager.convert_json_to_yaml(json_str)
        self.assertEqual(result, expected)

    def test_convert_json_to_yaml_file(self):
        json_str = '{"key": "value", "list": [1, 2]}'
        expected = yaml.dump({"key": "value", "list": [1, 2]}, sort_keys=False, default_flow_style=False)

        with NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name

        try:
            result = self.manager.convert_json_to_yaml(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_convert_json_to_yaml_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.convert_json_to_yaml("{invalid")


class TestYaml2JsonCLI(unittest.TestCase):
    def test_run_yaml2json(self):
        args = DummyArgs(action="yaml2json", input="key: value", output=None)
        self.assertTrue(run_yaml2json_lab_logic(args))

    def test_run_json2yaml(self):
        args = DummyArgs(action="json2yaml", input='{"key": "value"}', output=None)
        self.assertTrue(run_yaml2json_lab_logic(args))


if __name__ == '__main__':
    unittest.main()
