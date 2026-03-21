def process_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Remove all empty lines at the end, then add exactly one
    while lines and lines[-1].strip() == '':
        lines.pop()
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'

    with open(filepath, 'w') as f:
        f.writelines(lines)

for f in ["shared/typegen_lab.py", "shared/tui_typegen.py", "tests/test_typegen_lab.py", "tests/test_tui_typegen.py"]:
    process_file(f)
