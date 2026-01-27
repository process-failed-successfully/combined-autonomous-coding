import ast
import unittest
from pathlib import Path
from unittest.mock import patch
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
        node1.dependencies.add("b")  # implies b.py

        node2 = CodeNode("b.py", "module", "b.py", 1)

        map_data = {"a.py": node1, "b.py": node2}

        diagram = generate_mermaid(map_data)

        self.assertIn("classDiagram", diagram)
        self.assertIn("class a_py", diagram)
        self.assertIn("class b_py", diagram)
        self.assertIn("a_py ..> b_py : imports", diagram)

    def test_scan_project(self):
        import tempfile

        # Create a temporary directory and a python file inside it
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_path = temp_path / "test.py"
            file_path.write_text("def foo(): pass", encoding="utf-8")

            # Mock get_python_files to return our temp file
            with patch("shared.map.get_python_files") as mock_get_files:
                mock_get_files.return_value = [file_path]
                result = scan_project(temp_path)

                # The key in map_data is rel_path.
                # In scan_project, rel_path comes from file_path.relative_to(project_dir)
                # Here project_dir is temp_path.

                self.assertIn("test.py", result)
                self.assertEqual(result["test.py"].children[0].name, "foo")

    def test_end_lineno_capture(self):
        code = """
def single_line(): pass

def multi_line():
    x = 1
    return x
"""
        tree = ast.parse(code)
        builder = PythonMapBuilder(Path("test.py"), Path("."))
        builder.visit(tree)

        module_node = builder.module_node
        self.assertEqual(len(module_node.children), 2)

        single = next(c for c in module_node.children if c.name == "single_line")
        multi = next(c for c in module_node.children if c.name == "multi_line")

        # Python < 3.8 might not have end_lineno, but assuming CI environment is modern
        # If it's none, we assert it's None. If it's int, we check value.
        if hasattr(tree.body[0], 'end_lineno'):
            self.assertEqual(single.lineno, 2)
            self.assertEqual(single.end_lineno, 2)

            self.assertEqual(multi.lineno, 4)
            self.assertEqual(multi.end_lineno, 6)
        else:
            print("Skipping end_lineno test due to old Python version")


if __name__ == "__main__":
    unittest.main()
