import secrets
import random
import uuid
import sys
import string
from pathlib import Path
from typing import List, Any, Union, Optional

class RandomLabManager:
    """
    Manages random data generation.
    """

    def generate_int(self, min_val: int, max_val: int, count: int = 1) -> List[int]:
        """Generates random integers."""
        # Using secrets.randbelow for cryptographic strength where possible,
        # but for arbitrary ranges, random.SystemRandom is convenient.
        # SystemRandom uses os.urandom.
        rng = random.SystemRandom()
        return [rng.randint(min_val, max_val) for _ in range(count)]

    def generate_float(self, min_val: float, max_val: float, count: int = 1) -> List[float]:
        """Generates random floats."""
        rng = random.SystemRandom()
        return [rng.uniform(min_val, max_val) for _ in range(count)]

    def generate_string(self, length: int, charset: str, count: int = 1) -> List[str]:
        """Generates random strings."""
        chars = ""
        if charset == "alpha":
            chars = string.ascii_letters
        elif charset == "numeric":
            chars = string.digits
        elif charset == "alnum":
            chars = string.ascii_letters + string.digits
        elif charset == "hex":
            chars = string.hexdigits.lower()
        elif charset == "special":
            chars = string.punctuation
        elif charset == "all":
            chars = string.ascii_letters + string.digits + string.punctuation
        else:
            # Custom charset provided directly
            chars = charset

        if not chars:
            raise ValueError("Charset is empty.")

        results = []
        for _ in range(count):
            results.append("".join(secrets.choice(chars) for _ in range(length)))
        return results

    def choice(self, items: List[str], count: int = 1) -> List[str]:
        """Picks random items from a list."""
        if not items:
            raise ValueError("Item list is empty.")
        # secrets.choice only picks one. For multiple with replacement:
        return [secrets.choice(items) for _ in range(count)]

    def pick_lines(self, file_path: Union[str, Path], count: int = 1, unique: bool = False) -> List[str]:
        """Picks random lines from a file."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")

        lines = path.read_text(encoding="utf-8").splitlines()
        lines = [l for l in lines if l] # Filter empty lines? Maybe optional. Let's keep non-empty.

        if not lines:
            return []

        if unique:
            if count > len(lines):
                raise ValueError(f"Cannot pick {count} unique lines from file with only {len(lines)} lines.")
            # Use SystemRandom sample
            rng = random.SystemRandom()
            return rng.sample(lines, count)
        else:
            return [secrets.choice(lines) for _ in range(count)]

    def shuffle_lines(self, file_path: Union[str, Path, None]) -> List[str]:
        """Shuffles lines from a file or stdin."""
        lines = []
        if file_path and str(file_path) != "-":
            path = Path(file_path).resolve()
            if not path.exists():
                raise FileNotFoundError(f"File {path} not found.")
            lines = path.read_text(encoding="utf-8").splitlines()
        else:
            if not sys.stdin.isatty():
                content = sys.stdin.read()
                lines = content.splitlines()
            else:
                return [] # No input

        # Fisher-Yates shuffle using SystemRandom
        rng = random.SystemRandom()
        rng.shuffle(lines)
        return lines

    def generate_uuid(self, version: int = 4, count: int = 1) -> List[str]:
        """Generates UUIDs."""
        results = []
        for _ in range(count):
            if version == 4:
                results.append(str(uuid.uuid4()))
            elif version == 1:
                results.append(str(uuid.uuid1()))
            else:
                raise ValueError("Only UUID v1 and v4 are supported.")
        return results

    def flip_coin(self, count: int = 1) -> List[str]:
        """Flips a coin."""
        return [secrets.choice(["Heads", "Tails"]) for _ in range(count)]

    def roll_dice(self, sides: int = 6, count: int = 1) -> List[int]:
        """Rolls a dice."""
        rng = random.SystemRandom()
        return [rng.randint(1, sides) for _ in range(count)]


def run_random_lab_logic(args):
    """CLI logic for Random Lab."""
    manager = RandomLabManager()

    if args.action == "int":
        try:
            results = manager.generate_int(args.min, args.max, args.count)
            for r in results: print(r)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "float":
        try:
            results = manager.generate_float(args.min, args.max, args.count)
            for r in results: print(r)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "string":
        try:
            results = manager.generate_string(args.length, args.charset, args.count)
            for r in results: print(r)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "choice":
        try:
            results = manager.choice(args.items, args.count)
            for r in results: print(r)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "pick":
        try:
            results = manager.pick_lines(args.file, args.count, args.unique)
            for r in results: print(r)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "shuffle":
        try:
            results = manager.shuffle_lines(args.file)
            for r in results: print(r)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "uuid":
        try:
            results = manager.generate_uuid(args.version, args.count)
            for r in results: print(r)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "coin":
        results = manager.flip_coin(args.count)
        for r in results: print(r)

    elif args.action == "dice":
        results = manager.roll_dice(args.sides, args.count)
        for r in results: print(r)

    sys.exit(0)
