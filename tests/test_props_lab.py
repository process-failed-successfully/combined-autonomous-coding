import unittest
import json
import yaml
from shared.props_lab import PropsLabManager


class TestPropsLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = PropsLabManager()

    def test_parse_props_simple(self):
        props = """
key1=value1
key2:value2
 key3 = value3
        """
        result = self.manager.parse_props(props)
        self.assertEqual(result, {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })

    def test_parse_props_comments_and_empty(self):
        props = """
# comment
! comment
key1=value1

key2=value2
        """
        result = self.manager.parse_props(props)
        self.assertEqual(result, {
            "key1": "value1",
            "key2": "value2"
        })

    def test_parse_props_line_continuation(self):
        props = """
targetCity=\\
        Detroit
targetState=\\
  Michigan\\
  is\\
  great
        """
        result = self.manager.parse_props(props)
        self.assertEqual(result, {
            "targetCity": "Detroit",
            "targetState": "Michiganisgreat"
        })

    def test_parse_props_escapes(self):
        props = """
key\\\\with\\\\slashes=val\\\\nnewline
unicode=\\u00A9
        """
        result = self.manager.parse_props(props)
        self.assertEqual(result, {
            "key\\with\\slashes": "val\\nnewline",
            "unicode": "©"
        })

    def test_flatten_dict_simple(self):
        data = {
            "app": {
                "name": "my-app",
                "version": 1.0
            },
            "server": {
                "port": 8080
            }
        }
        flat = self.manager.flatten_dict(data)
        self.assertEqual(flat, {
            "app.name": "my-app",
            "app.version": "1.0",
            "server.port": "8080"
        })

    def test_flatten_dict_with_lists(self):
        data = {
            "urls": ["http://example.com", "http://test.com"],
            "features": {
                "enabled": True
            }
        }
        flat = self.manager.flatten_dict(data)
        self.assertEqual(flat, {
            "urls[0]": "http://example.com",
            "urls[1]": "http://test.com",
            "features.enabled": "true"
        })

    def test_flatten_dict_with_value_collision(self):
        # Edge case: {"a": {"_value": "1", "b": "2"}}
        data = {
            "a": {
                "_value": "1",
                "b": "2"
            }
        }
        flat = self.manager.flatten_dict(data)
        self.assertEqual(flat, {
            "a": "1",
            "a.b": "2"
        })

    def test_unflatten_dict_simple(self):
        flat = {
            "app.name": "my-app",
            "app.version": "1.0",
            "server.port": "8080"
        }
        nested = self.manager.unflatten_dict(flat)
        self.assertEqual(nested, {
            "app": {
                "name": "my-app",
                "version": "1.0"
            },
            "server": {
                "port": "8080"
            }
        })

    def test_unflatten_dict_collision(self):
        flat = {
            "a": "1",
            "a.b": "2"
        }
        nested = self.manager.unflatten_dict(flat)
        self.assertEqual(nested, {
            "a": {
                "_value": "1",
                "b": "2"
            }
        })

    def test_props_to_json(self):
        props = "app.name=test\napp.port=8080"
        json_str = self.manager.props_to_json(props)
        data = json.loads(json_str)
        self.assertEqual(data, {
            "app": {
                "name": "test",
                "port": "8080"
            }
        })

    def test_json_to_props(self):
        json_str = '{"app": {"name": "test", "port": 8080}}'
        props = self.manager.json_to_props(json_str)
        self.assertIn("app.name=test", props)
        self.assertIn("app.port=8080", props)

    def test_props_to_yaml(self):
        props = "app.name=test\napp.port=8080"
        yaml_str = self.manager.props_to_yaml(props)
        data = yaml.safe_load(yaml_str)
        self.assertEqual(data, {
            "app": {
                "name": "test",
                "port": "8080"
            }
        })

    def test_yaml_to_props(self):
        yaml_str = """
app:
  name: test
  port: 8080
"""
        props = self.manager.yaml_to_props(yaml_str)
        self.assertIn("app.name=test", props)
        self.assertIn("app.port=8080", props)


if __name__ == '__main__':
    unittest.main()
