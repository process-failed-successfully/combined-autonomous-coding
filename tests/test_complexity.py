import unittest
from shared.complexity import calculate_complexity


class TestComplexity(unittest.TestCase):
    def test_simple_function(self):
        code = """
def simple():
    return True
"""
        functions = calculate_complexity(code)
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0]['name'], 'simple')
        self.assertEqual(functions[0]['complexity'], 1)

    def test_if_statement(self):
        code = """
def check(x):
    if x > 0:
        return True
    return False
"""
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 2)

    def test_if_else_statement(self):
        code = """
def check(x):
    if x > 0:
        return True
    else:
        return False
"""
        # McCabe complexity counts branches. if/else is 1 decision point, so complexity 2.
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 2)

    def test_elif_statement(self):
        code = """
def check(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
"""
        # 2 decision points (if, elif) -> complexity 3
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 3)

    def test_loops(self):
        code = """
def loop(items):
    for item in items:
        if item:
            print(item)
    while True:
        break
"""
        # For loop (+1), If inside (+1), While loop (+1) -> 1 + 1 + 1 + 1 = 4
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 4)

    def test_boolean_ops(self):
        code = """
def check(a, b):
    if a and b:
        return True
"""
        # if (+1), and (+1) -> 1 + 1 + 1 = 3
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 3)

    def test_nested_function(self):
        code = """
def outer():
    def inner():
        if True:
            pass
    if True:
        pass
"""
        functions = calculate_complexity(code)
        self.assertEqual(len(functions), 2)

        # Outer: Base(1) + If(1) = 2. It does NOT count complexity of inner function body.
        outer = next(f for f in functions if f['name'] == 'outer')
        self.assertEqual(outer['complexity'], 2)

        # Inner: Base(1) + If(1) = 2
        inner = next(f for f in functions if f['name'] == 'inner')
        self.assertEqual(inner['complexity'], 2)

    def test_async_function(self):
        code = """
async def fetch():
    async for x in y:
        pass
"""
        # Async func (Base 1) + Async For (1) = 2
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 2)

    def test_try_except(self):
        code = """
def safe():
    try:
        pass
    except ValueError:
        pass
    except TypeError:
        pass
"""
        # Try/Except is considered +1 per except handler
        # Base(1) + 2 handlers = 3
        functions = calculate_complexity(code)
        self.assertEqual(functions[0]['complexity'], 3)


if __name__ == '__main__':
    unittest.main()
