import statistics
import math
from typing import List, Dict, Any, Union

class NumberLabManager:
    """Manages Number Lab operations: conversions, prime checking, factors, and stats."""

    def parse(self, num_str: str) -> Union[int, float]:
        """Parses a string into an int or float, supporting common prefixes."""
        num_str = num_str.strip()
        if not num_str:
            raise ValueError("Empty string")

        # Try int first to handle bases
        try:
            return int(num_str, 0)
        except ValueError:
            pass

        # Fallback to float
        try:
            return float(num_str)
        except ValueError:
            raise ValueError(f"Could not parse '{num_str}' as a number.")

    def convert(self, num_str: str, base_to: int) -> str:
        """Converts a number string to another base (2, 8, 10, 16)."""
        val = self.parse(num_str)
        if isinstance(val, float):
            # Only exact integers can be converted to other bases simply here
            if not val.is_integer():
                raise ValueError("Cannot convert fractional numbers to other bases in this tool.")
            val = int(val)

        if base_to == 2:
            return bin(val)
        elif base_to == 8:
            return oct(val)
        elif base_to == 10:
            return str(val)
        elif base_to == 16:
            return hex(val)
        else:
            raise ValueError(f"Unsupported base: {base_to}")

    def is_prime(self, num_str: str) -> bool:
        """Checks if a given number is prime."""
        val = self.parse(num_str)
        if isinstance(val, float):
            if not val.is_integer():
                return False
            val = int(val)

        if val < 2:
            return False
        if val in (2, 3):
            return True
        if val % 2 == 0 or val % 3 == 0:
            return False

        i = 5
        while i * i <= val:
            if val % i == 0 or val % (i + 2) == 0:
                return False
            i += 6
        return True

    def factors(self, num_str: str) -> List[int]:
        """Returns the prime factors of a given number."""
        val = self.parse(num_str)
        if isinstance(val, float):
            if not val.is_integer():
                raise ValueError("Cannot find prime factors of a fractional number.")
            val = int(val)

        if val < 2:
            return []

        factors = []
        # Count the number of 2s that divide val
        while val % 2 == 0:
            factors.append(2)
            val //= 2

        # val must be odd at this point
        for i in range(3, int(math.sqrt(val)) + 1, 2):
            while val % i == 0:
                factors.append(i)
                val //= i

        # This condition is to handle the case when val is a prime number greater than 2
        if val > 2:
            factors.append(val)

        return factors

    def stats(self, numbers_str: List[str]) -> Dict[str, Union[int, float]]:
        """Calculates statistical metrics for a list of numbers."""
        if not numbers_str:
            raise ValueError("Empty list of numbers.")

        numbers = [self.parse(num) for num in numbers_str]

        result: Dict[str, Union[int, float]] = {
            "count": len(numbers),
            "sum": sum(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "mean": statistics.mean(numbers),
        }

        if len(numbers) >= 2:
            result["median"] = statistics.median(numbers)
            try:
                result["mode"] = statistics.mode(numbers)
            except statistics.StatisticsError:
                pass # No unique mode

            result["variance"] = statistics.variance(numbers)
            result["stdev"] = statistics.stdev(numbers)

        return result

def run_number_lab_logic(args) -> bool:
    """CLI Entry point for Number Lab."""
    import sys
    manager = NumberLabManager()

    if args.action == "convert":
        if not args.number or not args.to_base:
            print("Error: --number and --to-base are required for conversion.", file=sys.stderr)
            return False
        try:
            result = manager.convert(args.number, int(args.to_base))
            print(f"Result: {result}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "prime":
        if not args.number:
            print("Error: --number is required.", file=sys.stderr)
            return False
        try:
            is_prime = manager.is_prime(args.number)
            if is_prime:
                print(f"{args.number} is a PRIME number.")
            else:
                print(f"{args.number} is NOT a prime number.")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "factors":
        if not args.number:
            print("Error: --number is required.", file=sys.stderr)
            return False
        try:
            factors = manager.factors(args.number)
            print(f"Prime factors of {args.number}: {', '.join(map(str, factors))}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "stats":
        if not args.numbers:
            print("Error: Provide at least one number for stats.", file=sys.stderr)
            return False
        try:
            stats = manager.stats(args.numbers)
            print("--- Statistics ---")
            for k, v in stats.items():
                print(f"{k.capitalize()}: {v}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    return True
