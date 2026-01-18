import ast
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.map import CodeNode, PythonMapBuilder, generate_mermaid, scan_project

class TestCodeMap(unittest.TestCase):
    def test_code_node_serialization(self):
        node = CodeNode("test_mod", "module", "test.py", 1)
        child = CodeNode("TestClass", "class", "test.py", 10)
        node.children.append(child)
        node.dependencies.add("os")

        data = node.to_dict()
        self.assertEqual(data["name"], "test_mod")
        self.assertEqual(data["type"], "module")
        self.assertEqual(len(data["children"]), 1)
        self.assertEqual(data["children"][0]["name"], "TestClass")
        self.assertEqual(data["dependencies"], ["os"])

    def test_python_map_builder(self):
        code = """
import os
from sys import path

class MyClass:
    def my_method(self):
        pass

def my_func():
    pass
"""
        tree = ast.parse(code)
        builder = PythonMapBuilder(Path("test.py"), Path("."))
        builder.visit(tree)

        module_node = builder.module_node
        self.assertEqual(module_node.name, "test.py")
        self.assertIn("os", module_node.dependencies)
        self.assertIn("sys", module_node.dependencies)

        self.assertEqual(len(module_node.children), 2)

        class_node = next(c for c in module_node.children if c.type == "class")
        self.assertEqual(class_node.name, "MyClass")
        self.assertEqual(len(class_node.children), 1)
        self.assertEqual(class_node.children[0].name, "my_method")

        func_node = next(c for c in module_node.children if c.type == "function")
        self.assertEqual(func_node.name, "my_func")

    def test_generate_mermaid(self):
        node1 = CodeNode("a.py", "module", "a.py", 1)
        node1.dependencies.add("b") # implies b.py

        node2 = CodeNode("b.py", "module", "b.py", 1)

        map_data = {"a.py": node1, "b.py": node2}

        diagram = generate_mermaid(map_data)

        self.assertIn("classDiagram", diagram)
        self.assertIn("class a_py", diagram)
        self.assertIn("class b_py", diagram)
        self.assertIn("a_py ..> b_py : imports", diagram)

    @patch("shared.map.get_python_files")
    def test_scan_project(self, mock_get_files):
        # Setup mock file system
        mock_file = MagicMock()
        mock_file.read_text.return_value = "def foo(): pass"
        mock_file.relative_to.return_value = "test.py"
        mock_get_files.return_value = [mock_file]

        result = scan_project(Path("."))

        self.assertIn("test.py", result)
        self.assertEqual(result["test.py"].children[0].name, "foo")

if __name__ == "__main__":
    unittest.main()
