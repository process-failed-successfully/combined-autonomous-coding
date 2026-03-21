def fix_file(path, replacements):
    with open(path, "r") as f:
        content = f.read()
    for o, n in replacements:
        content = content.replace(o, n)
    with open(path, "w") as f:
        f.write(content)

fix_file("shared/tui.py", [
    ("from shared.tui_typegen import TypegenLabTab\n", ""),
])

with open("shared/tui.py", "r") as f:
    lines = f.readlines()
with open("shared/tui.py", "w") as f:
    inserted = False
    for line in lines:
        f.write(line)
        if "from shared.tui_mac import MacLabTab" in line and not inserted:
            f.write("from shared.tui_typegen import TypegenLabTab\n")
            inserted = True
