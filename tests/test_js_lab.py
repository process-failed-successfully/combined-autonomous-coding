import unittest
import shutil
from shared.js_lab import JsLabManager

HAS_NODE = shutil.which("node") is not None

class TestJsLab(unittest.TestCase):
    def setUp(self):
        self.manager = JsLabManager()

    @unittest.skipIf(not HAS_NODE, "Node.js not installed")
    def test_run_code_success(self):
        code = 'console.log("Hello JS");'
        result = self.manager.run_code(code)

        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].strip(), "Hello JS")

    @unittest.skipIf(not HAS_NODE, "Node.js not installed")
    def test_run_code_error(self):
        code = 'console.log(undeclared_variable);'
        result = self.manager.run_code(code)

        self.assertFalse(result["success"])
        self.assertNotEqual(result["exit_code"], 0)
        self.assertIn("ReferenceError: undeclared_variable is not defined", result["stderr"])

    def test_minify(self):
        code = '''
        // This is a comment
        const url = "https://example.com";
        function add(a, b) {
            /* Block comment */
            return a + b;
        }
        '''
        result = self.manager.minify(code)

        self.assertTrue(result["success"])
        self.assertEqual(result["output"], 'const url = "https://example.com"; function add(a, b) { return a + b; }')

if __name__ == '__main__':
    unittest.main()
