import re

with open("main.py", "r") as f:
    text = f.read()

target = """    if args.command in ["nato-lab", "nato"]:
        run_nato_lab(args)"""

replacement = target + "\n        return"

if target in text and replacement not in text:
    text = text.replace(target, replacement)
    with open("main.py", "w") as f:
        f.write(text)
    print("Patched main.py")
