with open("shared/tui.py", "r") as f:
    content = f.read()

import_statement = "from shared.tui_uuid import UuidLabTab"
if "from shared.tui_ksuid import KsuidLabTab" not in content:
    content = content.replace(import_statement, "from shared.tui_ksuid import KsuidLabTab\n" + import_statement)

yield_statement = """            with TabPane("UUID Lab", id="tab-uuid"):
                yield UuidLabTab()"""

ksuid_yield = """            with TabPane("KSUID Lab", id="tab-ksuid"):
                yield KsuidLabTab()
"""

if 'with TabPane("KSUID Lab", id="tab-ksuid"):' not in content:
    content = content.replace(yield_statement, ksuid_yield + yield_statement)

with open("shared/tui.py", "w") as f:
    f.write(content)
