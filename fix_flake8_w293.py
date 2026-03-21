def process_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Strip trailing whitespace on each line
    lines = [line.rstrip() + '\n' for line in lines]

    # Remove excessive blank lines at EOF
    while len(lines) > 1 and lines[-1] == '\n' and lines[-2] == '\n':
        lines.pop()

    with open(filepath, 'w') as f:
        f.writelines(lines)

for f in ["shared/typegen_lab.py", "shared/tui_typegen.py", "tests/test_typegen_lab.py", "tests/test_tui_typegen.py"]:
    process_file(f)
