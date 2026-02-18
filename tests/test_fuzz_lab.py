import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from typing import List, Dict

# Ensure shared modules can be imported
sys.path.insert(0, str(Path(__file__).parents[1]))

from shared.fuzz_lab import FuzzLabManager, InputGenerator  # noqa: E402


# Dummy function for testing
def buggy_function(x: int, y: str):
    if x == 42:
        raise ValueError("Bug triggered!")
    if y == "crash":
        raise RuntimeError("Crash triggered!")


class TestInputGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = InputGenerator()

    def test_generate_int(self):
        val = self.generator.generate(int)
        self.assertIsInstance(val, int)

    def test_generate_str(self):
        val = self.generator.generate(str)
        self.assertIsInstance(val, str)

    def test_generate_list(self):
        val = self.generator.generate(List[int])
        self.assertIsInstance(val, list)
        if val:
            self.assertIsInstance(val[0], int)

    def test_generate_dict(self):
        val = self.generator.generate(Dict[str, int])
        self.assertIsInstance(val, dict)
        if val:
            k, v = next(iter(val.items()))
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, int)


class TestFuzzLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = FuzzLabManager(Path("."))

    def test_fuzz_function_crash(self):
        # We need to expose buggy_function in a module-like way or mock importlib
        # Easier: Create a temporary python file
        temp_file = Path("temp_fuzz_target.py")
        temp_file.write_text("""
def target(val: int):
    if val > 10:
        raise ValueError("Too high")
""")
        try:
            # We need to force the generator to eventually produce > 10
            # By default it's random. Let's patch the generator for this test.
            with patch.object(self.manager.generator, 'generate', return_value=100):
                failures = self.manager.fuzz_function("temp_fuzz_target.py", "target", count=5)

            self.assertTrue(len(failures) > 0)
            self.assertEqual(failures[0]["type"], "ValueError")
            self.assertIn("Too high", failures[0]["error"])

        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_fuzz_cli_crash(self):
        # Command that fails if input contains "fail"
        cmd = [sys.executable, "-c", "import sys; txt=sys.stdin.read(); sys.exit(1) if 'fail' in txt else sys.exit(0)"]
        cmd_str = " ".join(cmd)

        # Force generator to produce "fail"
        with patch.object(self.manager.generator, '_gen_str', return_value="this will fail"):
            crashes = self.manager.fuzz_cli(cmd_str, count=2, timeout=2)

        self.assertTrue(len(crashes) > 0)
        self.assertEqual(crashes[0]["return_code"], 1)


if __name__ == "__main__":
    unittest.main()
