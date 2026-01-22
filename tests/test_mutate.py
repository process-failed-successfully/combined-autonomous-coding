import unittest
import ast
from shared.mutate import MutationVisitor


class TestMutationVisitor(unittest.TestCase):
    def test_binop(self):
        code = "x = a + b"
        tree = ast.parse(code)
        visitor = MutationVisitor()
        visitor.visit(tree)
        self.assertEqual(len(visitor.mutations), 1)
        self.assertEqual(visitor.mutations[0].description, "Change + to -")

    def test_compare(self):
        code = "if a > b: pass"
        tree = ast.parse(code)
        visitor = MutationVisitor()
        visitor.visit(tree)
        # > -> <=, > -> >=
        self.assertEqual(len(visitor.mutations), 2)
        descriptions = [m.description for m in visitor.mutations]
        self.assertIn("Change > to <=", descriptions)
        self.assertIn("Change > to >=", descriptions)

    def test_constant(self):
        code = "x = True"
        tree = ast.parse(code)
        visitor = MutationVisitor()
        visitor.visit(tree)
        self.assertEqual(len(visitor.mutations), 1)
        self.assertEqual(visitor.mutations[0].description, "Change True to False")


if __name__ == '__main__':
    unittest.main()
