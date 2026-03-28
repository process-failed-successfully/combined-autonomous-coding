import unittest
import os
import yaml
import tomlkit
from tempfile import NamedTemporaryFile
from shared.yaml2toml_lab import Yaml2TomlManager, run_yaml2toml_lab_logic


class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestYaml2TomlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Yaml2TomlManager()

    def test_convert_yaml_to_toml_string(self):
        yaml_str = "key: value\nlist:\n  - 1\n  - 2"
        expected = tomlkit.dumps({"key": "value", "list": [1, 2]})
        result = self.manager.convert_yaml_to_toml(yaml_str)
        self.assertEqual(result, expected)

    def test_convert_yaml_to_toml_file(self):
        yaml_str = "key: value\nlist:\n  - 1\n  - 2"
        expected = tomlkit.dumps({"key": "value", "list": [1, 2]})

        with NamedTemporaryFile(mode='w', delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_str)
            tmp_path = tmp.name

        try:
            result = self.manager.convert_yaml_to_toml(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_convert_yaml_to_toml_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.convert_yaml_to_toml(":")

    def test_convert_yaml_to_toml_invalid_type(self):
        with self.assertRaises(ValueError):
            self.manager.convert_yaml_to_toml("- item")

    def test_convert_toml_to_yaml_string(self):
        toml_str = 'key = "value"\nlist = [1, 2]'
        expected = yaml.dump({"key": "value", "list": [1, 2]}, sort_keys=False, default_flow_style=False)
        result = self.manager.convert_toml_to_yaml(toml_str)
        self.assertEqual(result, expected)

    def test_convert_toml_to_yaml_file(self):
        toml_str = 'key = "value"\nlist = [1, 2]'
        expected = yaml.dump({"key": "value", "list": [1, 2]}, sort_keys=False, default_flow_style=False)

        with NamedTemporaryFile(mode='w', delete=False, suffix=".toml") as tmp:
            tmp.write(toml_str)
            tmp_path = tmp.name

        try:
            result = self.manager.convert_toml_to_yaml(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_convert_toml_to_yaml_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.convert_toml_to_yaml("key = ")


class TestYaml2TomlCLI(unittest.TestCase):
    def test_run_yaml2toml(self):
        args = DummyArgs(action="yaml2toml", input="key: value", output=None)
        self.assertTrue(run_yaml2toml_lab_logic(args))

    def test_run_toml2yaml(self):
        args = DummyArgs(action="toml2yaml", input='key = "value"', output=None)
        self.assertTrue(run_yaml2toml_lab_logic(args))


if __name__ == '__main__':
    unittest.main()
