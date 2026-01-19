import unittest
import shutil
import tempfile
from pathlib import Path
from shared.unused import UnusedCodeDetector

class TestUnusedCodeDetector(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content):
        path = self.test_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_unused_function(self):
        self.create_file("main.py", """
def used_func():
    pass

def unused_func():
    pass

used_func()
""")
        detector = UnusedCodeDetector(self.test_dir)
        detector.scan()
        unused = detector.get_unused_definitions()

        names = [x['name'] for x in unused]
        self.assertIn("unused_func", names)
        self.assertNotIn("used_func", names)

    def test_unused_class(self):
        self.create_file("models.py", """
class UsedClass:
    pass

class UnusedClass:
    pass

x = UsedClass()
""")
        detector = UnusedCodeDetector(self.test_dir)
        detector.scan()
        unused = detector.get_unused_definitions()

        names = [x['name'] for x in unused]
        self.assertIn("UnusedClass", names)
        self.assertNotIn("UsedClass", names)

    def test_cross_file_usage(self):
        self.create_file("lib.py", """
def helper():
    pass
""")
        self.create_file("app.py", """
from lib import helper
helper()
""")
        detector = UnusedCodeDetector(self.test_dir)
        detector.scan()
        unused = detector.get_unused_definitions()

        names = [x['name'] for x in unused]
        self.assertNotIn("helper", names)

    def test_ignore_pattern(self):
        self.create_file("ignore_me.py", """
def ignored_func():
    pass
""")
        detector = UnusedCodeDetector(self.test_dir, ignore_patterns=["ignore_me.py"])
        detector.scan()
        unused = detector.get_unused_definitions()

        # It shouldn't even be in definitions if ignored
        names = [x['name'] for x in unused]
        self.assertNotIn("ignored_func", names)

    def test_private_methods_not_skipped_by_default(self):
        # My implementation currently skips __name__, but not _name
        self.create_file("utils.py", """
def _internal():
    pass
""")
        detector = UnusedCodeDetector(self.test_dir)
        detector.scan()
        unused = detector.get_unused_definitions()
        names = [x['name'] for x in unused]
        self.assertIn("_internal", names)

if __name__ == '__main__':
    unittest.main()
