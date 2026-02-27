import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Comprehensive list of elements
ELEMENTS = {
    1: {"symbol": "H", "name": "Hydrogen", "mass": 1.008, "category": "diatomic nonmetal", "group": 1, "period": 1},
    2: {"symbol": "He", "name": "Helium", "mass": 4.0026, "category": "noble gas", "group": 18, "period": 1},
    3: {"symbol": "Li", "name": "Lithium", "mass": 6.94, "category": "alkali metal", "group": 1, "period": 2},
    4: {"symbol": "Be", "name": "Beryllium", "mass": 9.0122, "category": "alkaline earth metal", "group": 2, "period": 2},
    5: {"symbol": "B", "name": "Boron", "mass": 10.81, "category": "metalloid", "group": 13, "period": 2},
    6: {"symbol": "C", "name": "Carbon", "mass": 12.011, "category": "polyatomic nonmetal", "group": 14, "period": 2},
    7: {"symbol": "N", "name": "Nitrogen", "mass": 14.007, "category": "diatomic nonmetal", "group": 15, "period": 2},
    8: {"symbol": "O", "name": "Oxygen", "mass": 15.999, "category": "diatomic nonmetal", "group": 16, "period": 2},
    9: {"symbol": "F", "name": "Fluorine", "mass": 18.998, "category": "diatomic nonmetal", "group": 17, "period": 2},
    10: {"symbol": "Ne", "name": "Neon", "mass": 20.180, "category": "noble gas", "group": 18, "period": 2},
    11: {"symbol": "Na", "name": "Sodium", "mass": 22.990, "category": "alkali metal", "group": 1, "period": 3},
    12: {"symbol": "Mg", "name": "Magnesium", "mass": 24.305, "category": "alkaline earth metal", "group": 2, "period": 3},
    13: {"symbol": "Al", "name": "Aluminium", "mass": 26.982, "category": "post-transition metal", "group": 13, "period": 3},
    14: {"symbol": "Si", "name": "Silicon", "mass": 28.085, "category": "metalloid", "group": 14, "period": 3},
    15: {"symbol": "P", "name": "Phosphorus", "mass": 30.974, "category": "polyatomic nonmetal", "group": 15, "period": 3},
    16: {"symbol": "S", "name": "Sulfur", "mass": 32.06, "category": "polyatomic nonmetal", "group": 16, "period": 3},
    17: {"symbol": "Cl", "name": "Chlorine", "mass": 35.45, "category": "diatomic nonmetal", "group": 17, "period": 3},
    18: {"symbol": "Ar", "name": "Argon", "mass": 39.948, "category": "noble gas", "group": 18, "period": 3},
    19: {"symbol": "K", "name": "Potassium", "mass": 39.098, "category": "alkali metal", "group": 1, "period": 4},
    20: {"symbol": "Ca", "name": "Calcium", "mass": 40.078, "category": "alkaline earth metal", "group": 2, "period": 4},
    21: {"symbol": "Sc", "name": "Scandium", "mass": 44.956, "category": "transition metal", "group": 3, "period": 4},
    22: {"symbol": "Ti", "name": "Titanium", "mass": 47.867, "category": "transition metal", "group": 4, "period": 4},
    23: {"symbol": "V", "name": "Vanadium", "mass": 50.942, "category": "transition metal", "group": 5, "period": 4},
    24: {"symbol": "Cr", "name": "Chromium", "mass": 51.996, "category": "transition metal", "group": 6, "period": 4},
    25: {"symbol": "Mn", "name": "Manganese", "mass": 54.938, "category": "transition metal", "group": 7, "period": 4},
    26: {"symbol": "Fe", "name": "Iron", "mass": 55.845, "category": "transition metal", "group": 8, "period": 4},
    27: {"symbol": "Co", "name": "Cobalt", "mass": 58.933, "category": "transition metal", "group": 9, "period": 4},
    28: {"symbol": "Ni", "name": "Nickel", "mass": 58.693, "category": "transition metal", "group": 10, "period": 4},
    29: {"symbol": "Cu", "name": "Copper", "mass": 63.546, "category": "transition metal", "group": 11, "period": 4},
    30: {"symbol": "Zn", "name": "Zinc", "mass": 65.38, "category": "transition metal", "group": 12, "period": 4},
    31: {"symbol": "Ga", "name": "Gallium", "mass": 69.723, "category": "post-transition metal", "group": 13, "period": 4},
    32: {"symbol": "Ge", "name": "Germanium", "mass": 72.63, "category": "metalloid", "group": 14, "period": 4},
    33: {"symbol": "As", "name": "Arsenic", "mass": 74.922, "category": "metalloid", "group": 15, "period": 4},
    34: {"symbol": "Se", "name": "Selenium", "mass": 78.96, "category": "polyatomic nonmetal", "group": 16, "period": 4},
    35: {"symbol": "Br", "name": "Bromine", "mass": 79.904, "category": "diatomic nonmetal", "group": 17, "period": 4},
    36: {"symbol": "Kr", "name": "Krypton", "mass": 83.798, "category": "noble gas", "group": 18, "period": 4},
    37: {"symbol": "Rb", "name": "Rubidium", "mass": 85.468, "category": "alkali metal", "group": 1, "period": 5},
    38: {"symbol": "Sr", "name": "Strontium", "mass": 87.62, "category": "alkaline earth metal", "group": 2, "period": 5},
    39: {"symbol": "Y", "name": "Yttrium", "mass": 88.906, "category": "transition metal", "group": 3, "period": 5},
    40: {"symbol": "Zr", "name": "Zirconium", "mass": 91.224, "category": "transition metal", "group": 4, "period": 5},
    41: {"symbol": "Nb", "name": "Niobium", "mass": 92.906, "category": "transition metal", "group": 5, "period": 5},
    42: {"symbol": "Mo", "name": "Molybdenum", "mass": 95.95, "category": "transition metal", "group": 6, "period": 5},
    43: {"symbol": "Tc", "name": "Technetium", "mass": 98, "category": "transition metal", "group": 7, "period": 5},
    44: {"symbol": "Ru", "name": "Ruthenium", "mass": 101.07, "category": "transition metal", "group": 8, "period": 5},
    45: {"symbol": "Rh", "name": "Rhodium", "mass": 102.91, "category": "transition metal", "group": 9, "period": 5},
    46: {"symbol": "Pd", "name": "Palladium", "mass": 106.42, "category": "transition metal", "group": 10, "period": 5},
    47: {"symbol": "Ag", "name": "Silver", "mass": 107.87, "category": "transition metal", "group": 11, "period": 5},
    48: {"symbol": "Cd", "name": "Cadmium", "mass": 112.41, "category": "transition metal", "group": 12, "period": 5},
    49: {"symbol": "In", "name": "Indium", "mass": 114.82, "category": "post-transition metal", "group": 13, "period": 5},
    50: {"symbol": "Sn", "name": "Tin", "mass": 118.71, "category": "post-transition metal", "group": 14, "period": 5},
    51: {"symbol": "Sb", "name": "Antimony", "mass": 121.76, "category": "metalloid", "group": 15, "period": 5},
    52: {"symbol": "Te", "name": "Tellurium", "mass": 127.60, "category": "metalloid", "group": 16, "period": 5},
    53: {"symbol": "I", "name": "Iodine", "mass": 126.90, "category": "diatomic nonmetal", "group": 17, "period": 5},
    54: {"symbol": "Xe", "name": "Xenon", "mass": 131.29, "category": "noble gas", "group": 18, "period": 5},
    55: {"symbol": "Cs", "name": "Caesium", "mass": 132.91, "category": "alkali metal", "group": 1, "period": 6},
    56: {"symbol": "Ba", "name": "Barium", "mass": 137.33, "category": "alkaline earth metal", "group": 2, "period": 6},
    57: {"symbol": "La", "name": "Lanthanum", "mass": 138.91, "category": "lanthanide", "group": 3, "period": 6},
    58: {"symbol": "Ce", "name": "Cerium", "mass": 140.12, "category": "lanthanide", "group": 3, "period": 6},
    59: {"symbol": "Pr", "name": "Praseodymium", "mass": 140.91, "category": "lanthanide", "group": 3, "period": 6},
    60: {"symbol": "Nd", "name": "Neodymium", "mass": 144.24, "category": "lanthanide", "group": 3, "period": 6},
    61: {"symbol": "Pm", "name": "Promethium", "mass": 145, "category": "lanthanide", "group": 3, "period": 6},
    62: {"symbol": "Sm", "name": "Samarium", "mass": 150.36, "category": "lanthanide", "group": 3, "period": 6},
    63: {"symbol": "Eu", "name": "Europium", "mass": 151.96, "category": "lanthanide", "group": 3, "period": 6},
    64: {"symbol": "Gd", "name": "Gadolinium", "mass": 157.25, "category": "lanthanide", "group": 3, "period": 6},
    65: {"symbol": "Tb", "name": "Terbium", "mass": 158.93, "category": "lanthanide", "group": 3, "period": 6},
    66: {"symbol": "Dy", "name": "Dysprosium", "mass": 162.50, "category": "lanthanide", "group": 3, "period": 6},
    67: {"symbol": "Ho", "name": "Holmium", "mass": 164.93, "category": "lanthanide", "group": 3, "period": 6},
    68: {"symbol": "Er", "name": "Erbium", "mass": 167.26, "category": "lanthanide", "group": 3, "period": 6},
    69: {"symbol": "Tm", "name": "Thulium", "mass": 168.93, "category": "lanthanide", "group": 3, "period": 6},
    70: {"symbol": "Yb", "name": "Ytterbium", "mass": 173.05, "category": "lanthanide", "group": 3, "period": 6},
    71: {"symbol": "Lu", "name": "Lutetium", "mass": 174.97, "category": "lanthanide", "group": 3, "period": 6},
    72: {"symbol": "Hf", "name": "Hafnium", "mass": 178.49, "category": "transition metal", "group": 4, "period": 6},
    73: {"symbol": "Ta", "name": "Tantalum", "mass": 180.95, "category": "transition metal", "group": 5, "period": 6},
    74: {"symbol": "W", "name": "Tungsten", "mass": 183.84, "category": "transition metal", "group": 6, "period": 6},
    75: {"symbol": "Re", "name": "Rhenium", "mass": 186.21, "category": "transition metal", "group": 7, "period": 6},
    76: {"symbol": "Os", "name": "Osmium", "mass": 190.23, "category": "transition metal", "group": 8, "period": 6},
    77: {"symbol": "Ir", "name": "Iridium", "mass": 192.22, "category": "transition metal", "group": 9, "period": 6},
    78: {"symbol": "Pt", "name": "Platinum", "mass": 195.08, "category": "transition metal", "group": 10, "period": 6},
    79: {"symbol": "Au", "name": "Gold", "mass": 196.97, "category": "transition metal", "group": 11, "period": 6},
    80: {"symbol": "Hg", "name": "Mercury", "mass": 200.59, "category": "transition metal", "group": 12, "period": 6},
    81: {"symbol": "Tl", "name": "Thallium", "mass": 204.38, "category": "post-transition metal", "group": 13, "period": 6},
    82: {"symbol": "Pb", "name": "Lead", "mass": 207.2, "category": "post-transition metal", "group": 14, "period": 6},
    83: {"symbol": "Bi", "name": "Bismuth", "mass": 208.98, "category": "post-transition metal", "group": 15, "period": 6},
    84: {"symbol": "Po", "name": "Polonium", "mass": 209, "category": "post-transition metal", "group": 16, "period": 6},
    85: {"symbol": "At", "name": "Astatine", "mass": 210, "category": "metalloid", "group": 17, "period": 6},
    86: {"symbol": "Rn", "name": "Radon", "mass": 222, "category": "noble gas", "group": 18, "period": 6},
    87: {"symbol": "Fr", "name": "Francium", "mass": 223, "category": "alkali metal", "group": 1, "period": 7},
    88: {"symbol": "Ra", "name": "Radium", "mass": 226, "category": "alkaline earth metal", "group": 2, "period": 7},
    89: {"symbol": "Ac", "name": "Actinium", "mass": 227, "category": "actinide", "group": 3, "period": 7},
    90: {"symbol": "Th", "name": "Thorium", "mass": 232.04, "category": "actinide", "group": 3, "period": 7},
    91: {"symbol": "Pa", "name": "Protactinium", "mass": 231.04, "category": "actinide", "group": 3, "period": 7},
    92: {"symbol": "U", "name": "Uranium", "mass": 238.03, "category": "actinide", "group": 3, "period": 7},
    93: {"symbol": "Np", "name": "Neptunium", "mass": 237, "category": "actinide", "group": 3, "period": 7},
    94: {"symbol": "Pu", "name": "Plutonium", "mass": 244, "category": "actinide", "group": 3, "period": 7},
    95: {"symbol": "Am", "name": "Americium", "mass": 243, "category": "actinide", "group": 3, "period": 7},
    96: {"symbol": "Cm", "name": "Curium", "mass": 247, "category": "actinide", "group": 3, "period": 7},
    97: {"symbol": "Bk", "name": "Berkelium", "mass": 247, "category": "actinide", "group": 3, "period": 7},
    98: {"symbol": "Cf", "name": "Californium", "mass": 251, "category": "actinide", "group": 3, "period": 7},
    99: {"symbol": "Es", "name": "Einsteinium", "mass": 252, "category": "actinide", "group": 3, "period": 7},
    100: {"symbol": "Fm", "name": "Fermium", "mass": 257, "category": "actinide", "group": 3, "period": 7},
    101: {"symbol": "Md", "name": "Mendelevium", "mass": 258, "category": "actinide", "group": 3, "period": 7},
    102: {"symbol": "No", "name": "Nobelium", "mass": 259, "category": "actinide", "group": 3, "period": 7},
    103: {"symbol": "Lr", "name": "Lawrencium", "mass": 262, "category": "actinide", "group": 3, "period": 7},
    104: {"symbol": "Rf", "name": "Rutherfordium", "mass": 267, "category": "transition metal", "group": 4, "period": 7},
    105: {"symbol": "Db", "name": "Dubnium", "mass": 268, "category": "transition metal", "group": 5, "period": 7},
    106: {"symbol": "Sg", "name": "Seaborgium", "mass": 271, "category": "transition metal", "group": 6, "period": 7},
    107: {"symbol": "Bh", "name": "Bohrium", "mass": 272, "category": "transition metal", "group": 7, "period": 7},
    108: {"symbol": "Hs", "name": "Hassium", "mass": 270, "category": "transition metal", "group": 8, "period": 7},
    109: {"symbol": "Mt", "name": "Meitnerium", "mass": 276, "category": "transition metal", "group": 9, "period": 7},
    110: {"symbol": "Ds", "name": "Darmstadtium", "mass": 281, "category": "transition metal", "group": 10, "period": 7},
    111: {"symbol": "Rg", "name": "Roentgenium", "mass": 280, "category": "transition metal", "group": 11, "period": 7},
    112: {"symbol": "Cn", "name": "Copernicium", "mass": 285, "category": "transition metal", "group": 12, "period": 7},
    113: {"symbol": "Nh", "name": "Nihonium", "mass": 284, "category": "post-transition metal", "group": 13, "period": 7},
    114: {"symbol": "Fl", "name": "Flerovium", "mass": 289, "category": "post-transition metal", "group": 14, "period": 7},
    115: {"symbol": "Mc", "name": "Moscovium", "mass": 288, "category": "post-transition metal", "group": 15, "period": 7},
    116: {"symbol": "Lv", "name": "Livermorium", "mass": 293, "category": "post-transition metal", "group": 16, "period": 7},
    117: {"symbol": "Ts", "name": "Tennessine", "mass": 294, "category": "metalloid", "group": 17, "period": 7},
    118: {"symbol": "Og", "name": "Oganesson", "mass": 294, "category": "noble gas", "group": 18, "period": 7},
}

class ChemistryLabManager:
    """Manages chemistry operations like element lookup and molar mass calculation."""

    def __init__(self):
        # Create lookup maps
        self.symbol_map = {data["symbol"].lower(): num for num, data in ELEMENTS.items()}
        self.name_map = {data["name"].lower(): num for num, data in ELEMENTS.items()}

    def get_element(self, identifier: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Retrieves element details by symbol, name, or atomic number."""
        num = None
        if isinstance(identifier, int):
            num = identifier
        elif isinstance(identifier, str):
            if identifier.isdigit():
                num = int(identifier)
            else:
                lowered = identifier.lower()
                num = self.symbol_map.get(lowered) or self.name_map.get(lowered)

        if num and num in ELEMENTS:
            element = ELEMENTS[num].copy()
            element["atomic_number"] = num
            return element
        return None

    def search_elements(self, query: str) -> List[Dict[str, Any]]:
        """Search elements matching the query string in name, symbol or category."""
        query = query.lower()
        results = []
        for num, data in ELEMENTS.items():
            if (query in data["name"].lower() or
                query in data["symbol"].lower() or
                query in data["category"].lower()):
                element = data.copy()
                element["atomic_number"] = num
                results.append(element)
        return results

    def calculate_molar_mass(self, formula: str) -> Union[float, str]:
        """Calculates molar mass from a chemical formula (e.g. H2O, C6H12O6)."""
        if not formula:
            return 0.0

        # Pre-check for invalid characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()")
        if not all(c in valid_chars for c in formula):
             return f"Error: Invalid characters in formula."

        try:
            # Check for parens
            if '(' in formula or ')' in formula:
                return self._calculate_molar_mass_with_parens(formula)

            # Simple parser for "H2O", "C6H12O6", "NaCl"
            # Regex: ([A-Z][a-z]*)(\d*)

            tokens = re.findall(r'([A-Z][a-z]*)(\d*)', formula)

            # Validate coverage
            reconstructed = "".join([f"{s}{c}" for s, c in tokens])
            if reconstructed != formula:
                 return f"Error: Failed to parse formula '{formula}' completely."

            total_mass = 0.0
            for symbol, count_str in tokens:
                count = int(count_str) if count_str else 1
                element = self.get_element(symbol)
                if not element:
                    return f"Error: Unknown element symbol '{symbol}'"

                total_mass += element["mass"] * count

            return total_mass

        except Exception as e:
            return f"Error calculating mass: {e}"

    def _calculate_molar_mass_with_parens(self, formula: str) -> Union[float, str]:
        """Handles formulas with parentheses like Ca(OH)2 or (NH4)2SO4."""
        # Regex to split everything: ([A-Z][a-z]*|\d+|\(|\))
        tokens = re.findall(r'([A-Z][a-z]*|\d+|\(|\))', formula)

        # Validate reconstruction
        if "".join(tokens) != formula:
             return f"Error: Failed to tokenize formula '{formula}'"

        try:
            # We use a stack of counters (masses)
            # Each level on stack is a current mass accumulation for that group
            mass_stack = [0.0]

            idx = 0
            while idx < len(tokens):
                token = tokens[idx]

                if token == '(':
                    mass_stack.append(0.0)
                    idx += 1
                elif token == ')':
                    # End of group. Check next token for multiplier
                    current_group_mass = mass_stack.pop()
                    multiplier = 1
                    if idx + 1 < len(tokens) and tokens[idx+1].isdigit():
                        multiplier = int(tokens[idx+1])
                        idx += 1 # Skip number

                    if not mass_stack:
                         return "Error: Unbalanced parentheses"

                    mass_stack[-1] += current_group_mass * multiplier
                    idx += 1
                elif token.isdigit():
                    return f"Error: Unexpected number '{token}' at pos {idx}"
                else:
                    # Element symbol
                    element = self.get_element(token)
                    if not element:
                        return f"Error: Unknown element '{token}'"

                    elem_mass = element["mass"]
                    multiplier = 1
                    if idx + 1 < len(tokens) and tokens[idx+1].isdigit():
                        multiplier = int(tokens[idx+1])
                        idx += 1 # Skip number

                    mass_stack[-1] += elem_mass * multiplier
                    idx += 1

            if len(mass_stack) != 1:
                return "Error: Unbalanced parentheses"

            return mass_stack[0]

        except Exception as e:
            return f"Error parsing formula: {e}"

def run_chemistry_lab_logic(args):
    """CLI Entry point for Chemistry Lab."""
    manager = ChemistryLabManager()

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Chemistry Lab TUI...")
        project_dir = getattr(args, 'project_dir', Path("."))
        app = AgentTUI(project_dir=project_dir, start_tab="tab-chemistry")
        app.run()
        sys.exit(0)

    elif args.action == "info":
        if not args.element:
            print("Error: --element required for info.")
            sys.exit(1)

        el = manager.get_element(args.element)
        if el:
            print(f"--- {el['name']} ({el['symbol']}) ---")
            print(f"Atomic Number: {el['atomic_number']}")
            print(f"Atomic Mass:   {el['mass']}")
            print(f"Category:      {el['category']}")
            print(f"Group:         {el['group']}")
            print(f"Period:        {el['period']}")
        else:
            print(f"Element '{args.element}' not found.")
            sys.exit(1)

    elif args.action == "mass":
        if not args.formula:
            print("Error: --formula required for mass.")
            sys.exit(1)

        result = manager.calculate_molar_mass(args.formula)
        if isinstance(result, str): # Error message
            print(result)
            sys.exit(1)
        else:
            print(f"Molar Mass of {args.formula}: {result:.4f} g/mol")

    elif args.action == "list":
        print(f"{'#':<3} | {'Symbol':<4} | {'Name':<15} | {'Mass':<10} | {'Category'}")
        print("-" * 60)
        for num, data in ELEMENTS.items():
            print(f"{num:<3} | {data['symbol']:<4} | {data['name']:<15} | {data['mass']:<10} | {data['category']}")

    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
