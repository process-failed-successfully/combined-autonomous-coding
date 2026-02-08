import sys
from typing import Dict, Any, List, Optional, Tuple, Union


class UnitLabManager:
    """Manages Unit Lab operations: conversion between various units."""

    # Conversion tables relative to a base unit
    STORAGE: Dict[str, Union[int, float]] = {
        "b": 1, "byte": 1, "bytes": 1,
        "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
        "mb": 1024**2, "megabyte": 1024**2, "megabytes": 1024**2,
        "gb": 1024**3, "gigabyte": 1024**3, "gigabytes": 1024**3,
        "tb": 1024**4, "terabyte": 1024**4, "terabytes": 1024**4,
        "pb": 1024**5, "petabyte": 1024**5, "petabytes": 1024**5,
    }

    TIME: Dict[str, Union[int, float]] = {
        "ms": 0.001, "millisecond": 0.001, "milliseconds": 0.001,
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
        "m": 60, "min": 60, "minute": 60, "minutes": 60,
        "h": 3600, "hr": 3600, "hour": 3600, "hours": 3600,
        "d": 86400, "day": 86400, "days": 86400,
        "w": 604800, "week": 604800, "weeks": 604800,
        "y": 31536000, "year": 31536000, "years": 31536000,  # Approx (365 days)
    }

    LENGTH: Dict[str, Union[int, float]] = {
        "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
        "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
        "m": 1, "meter": 1, "meters": 1,
        "km": 1000, "kilometer": 1000, "kilometers": 1000,
        "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
        "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
        "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
        "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
    }

    WEIGHT: Dict[str, Union[int, float]] = {
        "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
        "g": 1, "gram": 1, "grams": 1,
        "kg": 1000, "kilogram": 1000, "kilograms": 1000,
        "oz": 28.34952, "ounce": 28.34952, "ounces": 28.34952,
        "lb": 453.59237, "pound": 453.59237, "pounds": 453.59237,
        "t": 1000000, "ton": 1000000, "tons": 1000000,  # Metric ton
    }

    TEMPERATURE: Dict[str, str] = {
        "c": "celsius", "celsius": "celsius",
        "f": "fahrenheit", "fahrenheit": "fahrenheit",
        "k": "kelvin", "kelvin": "kelvin",
    }

    CATEGORIES: Dict[str, Dict[str, Any]] = {
        "storage": STORAGE,
        "time": TIME,
        "length": LENGTH,
        "weight": WEIGHT,
        "temperature": TEMPERATURE,
    }

    def _resolve_category(self, unit: str, other_unit: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Identifies the category of a unit."""
        unit = unit.lower().strip()

        candidates = []
        for cat_name, table in self.CATEGORIES.items():
            if unit in table:
                candidates.append(cat_name)

        if not candidates:
            return None

        if len(candidates) > 1:
            # Ambiguity handling (e.g., 'm' for meter vs minute)

            # If we have a hint from the other unit, use it
            if other_unit:
                other_candidates = []
                for cat_name, table in self.CATEGORIES.items():
                    if other_unit.lower().strip() in table:
                        other_candidates.append(cat_name)

                # If there is an intersection between candidates and other_candidates, assume they share the category
                common = set(candidates).intersection(set(other_candidates))
                if common:
                    # Pick the common category
                    cat_name = list(common)[0]
                    return cat_name, self.CATEGORIES[cat_name]

            # Default logic if still ambiguous
            # Prioritize Length (meter) over Time (minute) for 'm' if no other context
            if "length" in candidates:
                return "length", self.LENGTH

            return candidates[0], self.CATEGORIES[candidates[0]]

        return candidates[0], self.CATEGORIES[candidates[0]]

    def convert(self, value: float, from_unit: str, to_unit: str) -> str:
        """Converts a value from one unit to another."""
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()

        # Identify category for both, using each other as hint
        cat1 = self._resolve_category(from_unit, other_unit=to_unit)
        cat2 = self._resolve_category(to_unit, other_unit=from_unit)

        if not cat1:
            return f"Error: Unknown unit '{from_unit}'."
        if not cat2:
            return f"Error: Unknown unit '{to_unit}'."

        if cat1[0] != cat2[0]:
            return f"Error: Cannot convert between {cat1[0]} ({from_unit}) and {cat2[0]} ({to_unit})."

        category, table = cat1

        # Temperature is special
        if category == "temperature":
            return self._convert_temperature(value, str(table[from_unit]), str(table[to_unit]))

        # Standard conversion via base unit
        # Cast to float for division
        from_factor = float(table[from_unit]) # type: ignore
        to_factor = float(table[to_unit]) # type: ignore

        # value * from_factor = base_value
        # base_value / to_factor = target_value
        result = (value * from_factor) / to_factor

        # Formatting: if close to int, show int, else float
        if result.is_integer():
            return f"{int(result)}"
        return f"{result:.4f}".rstrip('0').rstrip('.')

    def _convert_temperature(self, value: float, from_type: str, to_type: str) -> str:
        if from_type == to_type:
            return str(value)

        # Convert to Celsius first
        celsius = value
        if from_type == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_type == "kelvin":
            celsius = value - 273.15

        # Convert from Celsius to target
        result = celsius
        if to_type == "fahrenheit":
            result = (celsius * 9 / 5) + 32
        elif to_type == "kelvin":
            result = celsius + 273.15

        return f"{result:.2f}".rstrip('0').rstrip('.')

    def list_units(self, category: Optional[str] = None) -> List[str]:
        if category:
            cat = category.lower()
            if cat in self.CATEGORIES:
                return sorted(list(self.CATEGORIES[cat].keys()))
            else:
                return []

        # All units
        all_units: List[str] = []
        for table in self.CATEGORIES.values():
            all_units.extend(table.keys())
        return sorted(list(set(all_units)))


def run_unit_lab_logic(args) -> bool:
    """CLI handler for Unit Lab."""
    manager = UnitLabManager()

    if args.action == "convert":
        # Positional arguments in main.py will map to these
        # If user runs: unit convert 100 mb gb
        # args.value=100, args.from_unit=mb, args.to_unit=gb

        try:
            val = float(args.value)
        except ValueError:
            print(f"Error: Invalid value '{args.value}'. Must be a number.", file=sys.stderr)
            return False

        result = manager.convert(val, args.from_unit, args.to_unit)
        if result.startswith("Error"):
            print(result, file=sys.stderr)
            return False

        print(f"{result} {args.to_unit}")
        return True

    elif args.action == "list":
        cat = args.category
        units = manager.list_units(cat)
        if not units:
            print(f"No units found{f' for category {cat}' if cat else ''}.")
        else:
            print(f"Available Units{f' ({cat})' if cat else ''}:")
            import textwrap
            wrapped = textwrap.fill(", ".join(units), width=80)
            print(wrapped)
        return True

    return True
