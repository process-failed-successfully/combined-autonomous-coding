import argparse
import sys
import re

class ChmodLabManager:
    @staticmethod
    def parse(perm: str) -> dict:
        perm = perm.strip()
        octal = ""
        bin_str = ""
        sym = ""

        # Check if octal (3 or 4 digits)
        if re.match(r'^[0-7]{3,4}$', perm):
            octal_val = perm[-3:] # ignore SUID/SGID/sticky for basic view for now, just look at standard bits
            bin_str = bin(int(octal_val, 8))[2:].zfill(9)
        # Check if 9 char symbolic
        elif re.match(r'^[rwx-]{9}$', perm):
            bin_str = ""
            for char in perm:
                bin_str += "1" if char != "-" else "0"
        # Check if 10 char symbolic (like `drwxr-xr-x`)
        elif re.match(r'^.[rwx-]{9}$', perm):
            for char in perm[1:]:
                bin_str += "1" if char != "-" else "0"
        else:
            raise ValueError(f"Invalid permission format: '{perm}'. Expected 3-4 digit octal, or 9-10 char symbolic (e.g., 755 or rwxr-xr-x).")

        # Re-derive octal from binary
        octal = oct(int(bin_str, 2))[2:].zfill(3)

        # Re-derive sym from binary
        rwx_map = ['r', 'w', 'x']
        for i, b in enumerate(bin_str):
            if b == '1':
                sym += rwx_map[i % 3]
            else:
                sym += '-'

        # Breakdown strings
        def breakdown(section_bin: str) -> str:
            parts = []
            if section_bin[0] == '1': parts.append("read")
            if section_bin[1] == '1': parts.append("write")
            if section_bin[2] == '1': parts.append("execute")
            if not parts: return "none"
            return ", ".join(parts)

        owner = breakdown(bin_str[0:3])
        group = breakdown(bin_str[3:6])
        public = breakdown(bin_str[6:9])

        return {
            "octal": octal,
            "symbolic": sym,
            "binary": bin_str,
            "owner": owner,
            "group": group,
            "public": public
        }

def run_chmod_lab_logic(args: argparse.Namespace) -> bool:
    try:
        if getattr(args, "tui", False):
            from textual.app import App
            from shared.tui_chmod import ChmodLabTab
            from textual.widgets import TabbedContent, TabPane

            class TuiApp(App):
                def compose(self):
                    with TabbedContent():
                        with TabPane("Chmod Lab", id="chmod-lab-pane"):
                            yield ChmodLabTab()

            app = TuiApp()
            app.run()
            return True

        if not getattr(args, "permission", None):
            print("Error: must provide a permission string or --tui", file=sys.stderr)
            return False

        result = ChmodLabManager.parse(args.permission)
        print("Chmod Breakdown:")
        print(f"  Octal:    {result['octal']}")
        print(f"  Symbolic: {result['symbolic']}")
        print(f"  Binary:   {result['binary']}")
        print(f"  Owner:    {result['owner']}")
        print(f"  Group:    {result['group']}")
        print(f"  Public:   {result['public']}")
        return True
    except Exception as e:
        print(f"Error processing chmod: {e}", file=sys.stderr)
        return False
