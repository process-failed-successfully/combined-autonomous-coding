import unittest
from shared.brainfuck_lab import BrainfuckInterpreter

class TestBrainfuckLab(unittest.TestCase):
    def setUp(self):
        self.interpreter = BrainfuckInterpreter()

    def test_hello_world(self):
        code = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
        output = self.interpreter.run(code)
        self.assertEqual(output, "Hello World!\n")

    def test_input_output(self):
        code = ",."
        output = self.interpreter.run(code, input_data="A")
        self.assertEqual(output, "A")

    def test_addition(self):
        # 2 + 5 = 7
        # Cell 0 = 2, Cell 1 = 5, then add Cell 1 to Cell 0.
        code = "++>+++++[<+>-]<"
        self.interpreter.run(code)
        self.assertEqual(self.interpreter.memory[0], 7)

    def test_unmatched_brackets(self):
        with self.assertRaises(ValueError):
            self.interpreter.run("[")

        with self.assertRaises(ValueError):
            self.interpreter.run("]")

    def test_max_steps(self):
        code = "+[]" # infinite loop
        with self.assertRaises(RuntimeError):
            self.interpreter.run(code, max_steps=100)

if __name__ == '__main__':
    unittest.main()
