with open('shared/tui.py', 'r') as f:
    content = f.read()

import_statement = "from shared.tui_typegen import TypegenLabTab\n"
if "from shared.tui_typegen import TypegenLabTab" not in content:
    content = content.replace("from shared.tui_mac import MacLabTab\n", "from shared.tui_mac import MacLabTab\n" + import_statement)

tab_statement = """            with TabPane("Typegen Lab", id="tab-typegen"):
                yield TypegenLabTab()
"""
if "id=\"tab-typegen\"" not in content:
    content = content.replace("            with TabPane(\"Case Lab\", id=\"tab-case\"):\n                yield CaseLabTab()\n", "            with TabPane(\"Case Lab\", id=\"tab-case\"):\n                yield CaseLabTab()\n" + tab_statement)

with open('shared/tui.py', 'w') as f:
    f.write(content)
