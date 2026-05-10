import sys

with open("main.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "import sys; sys.exit(1)" in line:
        new_lines.append(line.replace("import sys; sys.exit(1)", "sys.exit(1)"))
    else:
        new_lines.append(line)

with open("main.py", "w") as f:
    f.writelines(new_lines)
