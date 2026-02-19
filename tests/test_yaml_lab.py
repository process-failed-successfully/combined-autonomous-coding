import unittest
from unittest.mock import MagicMock
from shared.yaml_lab import YamlLabManager
import yaml

class TestYamlLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = YamlLabManager()
        self.sample_data = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "test-pod",
                "labels": {
                    "app": "web",
                    "env": "prod"
                }
            },
            "spec": {
                "containers": [
                    {"name": "nginx", "image": "nginx:latest"},
                    {"name": "redis", "image": "redis:alpine"}
                ]
            }
        }

    def test_parse_path(self):
        self.assertEqual(self.manager._parse_path("a.b.c"), ["a", "b", "c"])
        self.assertEqual(self.manager._parse_path("a[0].b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("a.0.b"), ["a", 0, "b"])
        self.assertEqual(self.manager._parse_path("key"), ["key"])

    def test_get(self):
        self.assertEqual(self.manager.get(self.sample_data, "metadata.name"), "test-pod")
        self.assertEqual(self.manager.get(self.sample_data, "spec.containers[0].image"), "nginx:latest")
        self.assertEqual(self.manager.get(self.sample_data, "spec.containers[1].name"), "redis")

        # Test nonexistent keys
        self.assertIsNone(self.manager.get(self.sample_data, "metadata.namespace"))
        self.assertIsNone(self.manager.get(self.sample_data, "spec.containers[5]"))

    def test_set(self):
        # Set existing
        self.manager.set(self.sample_data, "metadata.labels.env", "dev")
        self.assertEqual(self.sample_data["metadata"]["labels"]["env"], "dev")

        # Set new key
        self.manager.set(self.sample_data, "metadata.labels.tier", "backend")
        self.assertEqual(self.sample_data["metadata"]["labels"]["tier"], "backend")

        # Set list index
        self.manager.set(self.sample_data, "spec.containers[0].image", "nginx:1.19")
        self.assertEqual(self.sample_data["spec"]["containers"][0]["image"], "nginx:1.19")

        # Create nested structure
        data = {}
        self.manager.set(data, "a.b.c", 1)
        self.assertEqual(data, {"a": {"b": {"c": 1}}})

        # Create list in path
        data = {}
        self.manager.set(data, "a[0].b", 1)
        self.assertEqual(data, {"a": [{"b": 1}]})

    def test_delete(self):
        # Delete dict key
        self.manager.delete(self.sample_data, "metadata.labels.env")
        self.assertNotIn("env", self.sample_data["metadata"]["labels"])

        # Delete list item
        self.manager.delete(self.sample_data, "spec.containers[0]")
        self.assertEqual(len(self.sample_data["spec"]["containers"]), 1)
        self.assertEqual(self.sample_data["spec"]["containers"][0]["name"], "redis")

    def test_merge(self):
        base = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": [1, 2]
        }
        override = {
            "b": {"c": 4},
            "e": [3],
            "f": 5
        }

        merged = self.manager.merge(base, override)

        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"]["c"], 4) # Overridden
        self.assertEqual(merged["b"]["d"], 3) # Preserved
        self.assertEqual(merged["e"], [3]) # List replaced, not merged (standard behavior for deep merge usually unless specialized)
        self.assertEqual(merged["f"], 5) # Added

    def test_to_json(self):
        data = {"a": 1, "b": "test"}
        json_str = self.manager.to_json(data)
        self.assertIn('"a": 1', json_str)
        self.assertIn('"b": "test"', json_str)

    def test_validate(self):
        valid_yaml = """
key: value
list:
  - item1
  - item2
"""
        self.assertTrue(self.manager.validate(valid_yaml))

        invalid_yaml = """
key: value
  indentation_error
"""
        # "key: value" followed by indented text might be parsed as multiline string if not careful,
        # but here it should be a mapping. "  indentation_error" is indented relative to "key".
        # PyYAML is actually quite permissible. Let's use something strictly invalid.
        # Unbalanced brackets are usually a safe bet for invalid syntax.
        invalid_yaml_2 = "[unbalanced brackets"
        self.assertFalse(self.manager.validate(invalid_yaml_2))

    def test_dump_yaml(self):
        data = {"a": 1, "b": [2, 3]}
        yaml_str = self.manager.dump_yaml(data)
        # Check basic YAML structure
        self.assertIn("a: 1", yaml_str)
        self.assertIn("b:", yaml_str)
        self.assertIn("- 2", yaml_str)

    def test_list_path_input(self):
        """Test that get/set/delete accept a list of keys/indices directly."""
        data = {
            "a": {
                "b": [10, 20, 30]
            }
        }

        # Test GET with list path
        path_list = ["a", "b", 1]
        self.assertEqual(self.manager.get(data, path_list), 20)

        # Test SET with list path
        self.manager.set(data, path_list, 99)
        self.assertEqual(data["a"]["b"][1], 99)

        # Test DELETE with list path
        self.manager.delete(data, ["a", "b", 1])
        self.assertEqual(data["a"]["b"], [10, 30])

if __name__ == '__main__':
    unittest.main()
