"""
Unit Lab
========

Utilities for unit conversion (bytes, time, temperature, length, weight).
"""

import sys
from typing import Dict, Any, List, Optional, Set
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class UnitLabManager:
    """Manages unit conversions."""

    CONVERSION_FACTORS: Dict[str, Dict[str, float]] = {
        "storage": {
            "b": 1.0,
            "kb": 1000.0,
            "mb": 1000.0**2,
            "gb": 1000.0**3,
            "tb": 1000.0**4,
            "pb": 1000.0**5,
            "kib": 1024.0,
            "mib": 1024.0**2,
            "gib": 1024.0**3,
            "tib": 1024.0**4,
            "pib": 1024.0**5,
        },
        "time": {
            "ms": 0.001,
            "s": 1.0,
            "m": 60.0,
            "min": 60.0,
            "h": 3600.0,
            "hr": 3600.0,
            "d": 86400.0,
            "day": 86400.0,
            "w": 604800.0,
            "week": 604800.0,
            "y": 31536000.0, # Approximate year (365 days)
            "year": 31536000.0,
        },
        "length": {
            "mm": 0.001,
            "cm": 0.01,
            "m": 1.0,
            "km": 1000.0,
            "in": 0.0254,
            "ft": 0.3048,
            "yd": 0.9144,
            "mi": 1609.34,
        },
        "weight": {
            "mg": 0.000001,
            "g": 0.001,
            "kg": 1.0,
            "oz": 0.0283495,
            "lb": 0.453592,
        },
    }

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Converts a value from one unit to another."""
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        # Check temperature first
        if from_unit in ["c", "f", "k"] or to_unit in ["c", "f", "k"]:
            # Ensure both are temp
            if from_unit in ["c", "f", "k"] and to_unit in ["c", "f", "k"]:
                return self._convert_temp(value, from_unit, to_unit)
            # Fallthrough to category check if one is not temp (will fail there)

        # Detect categories
        from_cats = self._get_categories(from_unit)
        to_cats = self._get_categories(to_unit)

        if not from_cats:
            raise ValueError(f"Unknown unit: {from_unit}")
        if not to_cats:
            raise ValueError(f"Unknown unit: {to_unit}")

        # Find common category
        common = set(from_cats).intersection(to_cats)

        if not common:
             raise ValueError(f"Incompatible units: {from_unit} and {to_unit}")

        # Pick the first common category
        category = list(common)[0]

        factors = self.CONVERSION_FACTORS[category]

        # Convert to base unit then to target unit
        base_value = value * factors[from_unit]
        return base_value / factors[to_unit]

    def _convert_temp(self, value: float, from_unit: str, to_unit: str) -> float:
        # Normalize to Celsius
        c_val = 0.0
        if from_unit == "c":
            c_val = value
        elif from_unit == "f":
            c_val = (value - 32) * 5/9
        elif from_unit == "k":
            c_val = value - 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # Convert from Celsius
        if to_unit == "c":
            return c_val
        elif to_unit == "f":
            return (c_val * 9/5) + 32
        elif to_unit == "k":
            return c_val + 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")

    def _get_categories(self, unit: str) -> List[str]:
        cats = []
        for cat, units in self.CONVERSION_FACTORS.items():
            if unit in units:
                cats.append(cat)
        if unit in ["c", "f", "k"]:
            cats.append("temperature")
        return cats

    def list_units(self, category: Optional[str] = None) -> None:
        """Prints available units."""
        cats = self.CONVERSION_FACTORS.copy()
        cats["temperature"] = {"c": 0, "f": 0, "k": 0} # dummy values

        if category:
            if category not in cats:
                console.print(f"[red]Category '{category}' not found.[/red]")
                return
            cats = {category: cats[category]}

        for cat, units in cats.items():
            console.print(f"[bold cyan]{cat.capitalize()}:[/bold cyan] {', '.join(sorted(units.keys()))}")


def run_unit_lab_logic(args):
    """Entry point for Unit Lab."""
    manager = UnitLabManager()

    if args.action == "convert":
        try:
            value = float(args.value)
            result = manager.convert(value, args.from_unit, args.to_unit)

            # Format nicely
            if abs(result) < 0.01:
                res_str = f"{result:.6f}"
            elif abs(result) < 1.0:
                res_str = f"{result:.4f}"
            else:
                res_str = f"{result:,.2f}"

            # Remove trailing zeros after decimal if any
            if "." in res_str:
                res_str = res_str.rstrip("0").rstrip(".")

            console.print(Panel(
                f"[bold green]{value} {args.from_unit}[/bold green] = [bold yellow]{res_str} {args.to_unit}[/bold yellow]",
                title="Conversion Result"
            ))
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected Error: {e}[/red]", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        manager.list_units(args.category)

    return True
