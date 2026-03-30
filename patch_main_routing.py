import sys

with open("main.py", "r") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    if "args.action = args.command" in line and "xml2toml" in lines[idx-1]:
        # we need to skip this block and replace it
        continue
    if "args.action = \"xml2toml\"" in line and "xml2toml-lab" in lines[idx-1]:
        continue
    if "if args.command in [\"xml2toml-lab\", \"x2t\"]:" in line and "args.action = args.command" in lines[idx-2]:
        continue

    new_lines.append(line)

# Let's just do a string replace to be safer
