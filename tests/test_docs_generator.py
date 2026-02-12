import unittest
import ast
import shutil
import tempfile
from pathlib import Path
from shared.docs_generator import DocsGenerator

class TestDocsGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = Path(tempfile.mkdtemp())
        self.generator = DocsGenerator(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def create_dummy_file(self, filename, content):
        path = self.test_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_parse_file_simple(self):
        code = """
'''Module docstring.'''

def my_func(a, b):
    '''Function docstring.'''
    pass

class MyClass:
    '''Class docstring.'''
    def method(self, x):
        '''Method docstring.'''
        pass
"""
        file_path = self.create_dummy_file("test_module.py", code)
        info = self.generator._parse_file(file_path)

        self.assertIsNotNone(info)
        self.assertEqual(info["docstring"].strip(), "Module docstring.")

        self.assertEqual(len(info["functions"]), 1)
        self.assertEqual(info["functions"][0]["name"], "my_func")
        self.assertEqual(info["functions"][0]["docstring"], "Function docstring.")
        self.assertEqual(info["functions"][0]["args"], ["a", "b"])

        self.assertEqual(len(info["classes"]), 1)
        self.assertEqual(info["classes"][0]["name"], "MyClass")
        self.assertEqual(info["classes"][0]["docstring"], "Class docstring.")

        self.assertEqual(len(info["classes"][0]["methods"]), 1)
        self.assertEqual(info["classes"][0]["methods"][0]["name"], "method")
        self.assertEqual(info["classes"][0]["methods"][0]["docstring"], "Method docstring.")
        self.assertEqual(info["classes"][0]["methods"][0]["args"], ["x"]) # self is excluded

    def test_scan_directory(self):
        self.create_dummy_file("main.py", "")
        self.create_dummy_file("utils/helper.py", "")

        structure = self.generator.scan(self.test_dir)

        self.assertIn("main", structure)
        self.assertIn("utils.helper", structure)

    def test_generate_files(self):
        code = """
def hello():
    '''Says hello.'''
    pass
"""
        self.create_dummy_file("hello.py", code)

        success = self.generator.generate(self.test_dir, self.output_dir)
        self.assertTrue(success)

        expected_doc = self.output_dir / "hello.md"
        self.assertTrue(expected_doc.exists())

        content = expected_doc.read_text(encoding="utf-8")
        self.assertIn("# Module: `hello`", content)
        self.assertIn("## Functions", content)
        self.assertIn("Says hello.", content)

        index_file = self.output_dir / "README.md"
        self.assertTrue(index_file.exists())
        index_content = index_file.read_text(encoding="utf-8")
        self.assertIn("[hello](hello.md)", index_content)

    def test_clean(self):
        (self.output_dir / "test.txt").touch()
        self.assertTrue(self.output_dir.exists())

        self.generator.clean(self.output_dir)
        self.assertFalse(self.output_dir.exists())

if __name__ == '__main__':
    unittest.main()
