import argparse
import sys
from typing import Dict, List, Tuple

class BrainfuckInterpreter:
    """An interpreter for the Brainfuck esoteric programming language."""

    def __init__(self, memory_size: int = 30000):
        self.memory_size = memory_size
        self.memory: List[int] = [0] * memory_size
        self.dp: int = 0  # Data pointer
        self.ip: int = 0  # Instruction pointer
        self.code: str = ""
        self.input_data: str = ""
        self.input_ptr: int = 0
        self.output_data: str = ""
        self.jumps: Dict[int, int] = {}
        self.steps: int = 0

    def reset(self) -> None:
        """Resets the state of the interpreter."""
        self.memory = [0] * self.memory_size
        self.dp = 0
        self.ip = 0
        self.output_data = ""
        self.input_ptr = 0
        self.steps = 0

    def load(self, code: str, input_data: str = "") -> None:
        """Loads Brainfuck code and optional input data."""
        self.reset()
        self.code = ''.join([c for c in code if c in "><+-.,[]"])
        self.input_data = input_data
        self._precompute_jumps()

    def _precompute_jumps(self) -> None:
        """Precomputes loop jumps for O(1) jump lookups."""
        self.jumps = {}
        stack = []
        for i, c in enumerate(self.code):
            if c == '[':
                stack.append(i)
            elif c == ']':
                if not stack:
                    raise ValueError(f"Unmatched ']' at position {i}")
                start = stack.pop()
                self.jumps[start] = i
                self.jumps[i] = start
        if stack:
            raise ValueError(f"Unmatched '[' at position {stack[-1]}")

    def step(self) -> bool:
        """Executes a single instruction. Returns True if continued, False if halted."""
        if self.ip >= len(self.code):
            return False

        c = self.code[self.ip]

        if c == '>':
            self.dp = (self.dp + 1) % self.memory_size
        elif c == '<':
            self.dp = (self.dp - 1) % self.memory_size
        elif c == '+':
            self.memory[self.dp] = (self.memory[self.dp] + 1) % 256
        elif c == '-':
            self.memory[self.dp] = (self.memory[self.dp] - 1) % 256
        elif c == '.':
            self.output_data += chr(self.memory[self.dp])
        elif c == ',':
            if self.input_ptr < len(self.input_data):
                self.memory[self.dp] = ord(self.input_data[self.input_ptr]) % 256
                self.input_ptr += 1
            else:
                self.memory[self.dp] = 0  # Standard behavior for EOF
        elif c == '[':
            if self.memory[self.dp] == 0:
                self.ip = self.jumps[self.ip]
        elif c == ']':
            if self.memory[self.dp] != 0:
                self.ip = self.jumps[self.ip]

        self.ip += 1
        self.steps += 1
        return True

    def run(self, code: str, input_data: str = "", max_steps: int = 1000000) -> str:
        """Runs Brainfuck code to completion."""
        self.load(code, input_data)

        while self.step() and self.steps < max_steps:
            pass

        if self.steps >= max_steps:
            raise RuntimeError(f"Exceeded maximum steps ({max_steps})")

        return self.output_data

def run_brainfuck_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Brainfuck Lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching Brainfuck Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-brainfuck")
        app.run()
        return True

    code = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r") as f:
                code = f.read()
        except IOError as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif getattr(args, "code", None):
        code = args.code
    else:
        print("Error: Either --code, --file, or --tui must be provided.", file=sys.stderr)
        return False

    input_data = getattr(args, "input", "")

    interpreter = BrainfuckInterpreter()
    try:
        output = interpreter.run(code, input_data)
        print(output, end="")
        return True
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return False
