import unittest
from pathlib import Path
from unittest.mock import MagicMock
from shared.map import CodeNode
from shared.code_query import filter_nodes, matches_pattern

class TestCodeQuery(unittest.TestCase):

    def test_matches_pattern(self):
        self.assertTrue(matches_pattern("FooBar", "Foo*"))
        self.assertTrue(matches_pattern("FooBar", "*Bar"))
        self.assertFalse(matches_pattern("FooBar", "Baz*"))
        self.assertTrue(matches_pattern("FooBar", "^Foo.*")) # Regex
        self.assertFalse(matches_pattern("FooBar", "^Bar.*")) # Regex

    def test_filter_nodes(self):
        # Setup tree
        # File A
        #   Class MyClass
        #     Method my_method
        #   Function my_func

        root = CodeNode("root", "module", "A.py", 0)

        cls = CodeNode("MyClass", "class", "A.py", 10)
        cls.bases = ["BaseClass"]
        cls.decorators = ["dataclass"]

        method = CodeNode("my_method", "function", "A.py", 12)
        method.decorators = ["property"]
        cls.children.append(method)

        func = CodeNode("my_func", "function", "A.py", 20)
        func.dependencies = {"os", "sys"}

        root.children.extend([cls, func])

        map_data = {"A.py": root}

        # Test 1: Filter by Type
        results = filter_nodes(map_data, type_filter="class")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "MyClass")

        # Test 2: Filter by Name
        results = filter_nodes(map_data, name_filter="my_*")
        self.assertEqual(len(results), 2)
        names = sorted([r["name"] for r in results])
        self.assertEqual(names, ["my_func", "my_method"])

        # Test 3: Filter by Base
        results = filter_nodes(map_data, base_filter="Base*")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "MyClass")

        # Test 4: Filter by Decorator
        results = filter_nodes(map_data, decorator_filter="prop*")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "my_method")

        # Test 5: Filter by Import
        # Note: Imports are usually on module level, but here func has dependencies
        results = filter_nodes(map_data, import_filter="os")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "my_func")

if __name__ == "__main__":
    unittest.main()
