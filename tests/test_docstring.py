import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from shared.docstring import DocstringManager


class TestDocstringManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = DocstringManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_finds_missing_docstrings(self):
        code = """
def func_no_doc():
    pass

def func_with_doc():
    "Doc"
    pass

class ClassNoDoc:
    def method_no_doc(self):
        pass

class ClassWithDoc:
    "Doc"
    pass

def oneliner(): pass
"""
        (self.test_dir / "test.py").write_text(code)

        items = self.manager.scan()

        # Expected: func_no_doc, ClassNoDoc, method_no_doc
        # oneliner should be skipped
        names = [item["name"] for item in items]
        self.assertIn("func_no_doc", names)
        self.assertIn("ClassNoDoc", names)
        self.assertIn("method_no_doc", names)
        self.assertNotIn("func_with_doc", names)
        self.assertNotIn("ClassWithDoc", names)
        self.assertNotIn("oneliner", names)

    def test_scan_ignores_dirs(self):
        (self.test_dir / "node_modules").mkdir()
        (self.test_dir / "node_modules" / "ignored.py").write_text("def ignore_me(): pass")

        items = self.manager.scan()
        self.assertEqual(len(items), 0)

    @patch("shared.docstring.GeminiAgent")
    async def test_generate_and_apply(self, MockAgent):
        # Setup mock agent
        mock_instance = MockAgent.return_value
        # Mock run_agent_session to return (status, response, actions)
        mock_instance.run_agent_session = AsyncMock(return_value=(True, '"""Generated Doc"""', []))

        code = """
def my_func(a, b):
    return a + b
"""
        p = self.test_dir / "target.py"
        p.write_text(code)

        items = self.manager.scan()
        self.assertEqual(len(items), 1)

        count = await self.manager.generate_and_apply(items, agent_type="gemini")

        self.assertEqual(count, 1)

        new_code = p.read_text()
        expected = """
def my_func(a, b):
    \"\"\"Generated Doc\"\"\"
    return a + b
"""
        self.assertEqual(new_code.strip(), expected.strip())

    @patch("shared.docstring.GeminiAgent")
    async def test_generate_and_apply_multiline(self, MockAgent):
        # Setup mock agent
        mock_instance = MockAgent.return_value
        # Return multiline docstring without quotes
        mock_instance.run_agent_session = AsyncMock(return_value=(True, 'Summary.\n\n    Args:\n        a: int', []))

        code = """
def my_func(a):
    print(a)
"""
        p = self.test_dir / "target.py"
        p.write_text(code)

        items = self.manager.scan()
        await self.manager.generate_and_apply(items, agent_type="gemini")

        new_code = p.read_text()

        # It should wrap in quotes and indent correctly
        self.assertIn('"""Summary.', new_code)
        self.assertIn('    Args:', new_code)


if __name__ == '__main__':
    unittest.main()
