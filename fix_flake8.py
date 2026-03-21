def process_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Strip trailing whitespace on each line
    lines = [line.rstrip('\n') + '\n' for line in lines]

    # Ensure correct whitespace at the end
    while lines and lines[-1] == '\n':
        lines.pop()
    lines.append('\n')

    # Specific replacements
    content = "".join(lines)
    # Remove unused typing
    content = content.replace("from typing import Any, Dict, List, Set\n", "from typing import Any, Dict\n")
    # Add two blank lines before classes
    content = content.replace("\nclass TypegenManager:", "\n\nclass TypegenManager:")
    content = content.replace("\nclass TypegenLabTab(Container):", "\n\nclass TypegenLabTab(Container):")
    content = content.replace("\nclass DummyApp(App[None]):", "\n\nclass DummyApp(App[None]):")
    content = content.replace("\nclass TestTypegenLabTab(unittest.IsolatedAsyncioTestCase):", "\n\nclass TestTypegenLabTab(unittest.IsolatedAsyncioTestCase):")
    content = content.replace("\nclass TestTypegenManager(unittest.TestCase):", "\n\nclass TestTypegenManager(unittest.TestCase):")
    content = content.replace("\nclass TestTypegenLabTabCLI(unittest.TestCase):", "\n\nclass TestTypegenLabTabCLI(unittest.TestCase):")
    content = content.replace("\nclass TestTypegenLabCLI(unittest.TestCase):", "\n\nclass TestTypegenLabCLI(unittest.TestCase):")
    content = content.replace("\ndef run_typegen_lab_logic(args):", "\n\ndef run_typegen_lab_logic(args):")
    content = content.replace("if __name__ == '__main__':", "\nif __name__ == '__main__':")
    content = content.replace("from textual import on, work\n", "from textual import on\n")
    content = content.replace("        if safe_key in [\"type\", \"match\", \"loop\", \"fn\", \"let\"]: # rust keywords", "        if safe_key in [\"type\", \"match\", \"loop\", \"fn\", \"let\"]:  # rust keywords")

    with open(filepath, 'w') as f:
        f.write(content)

for f in ["shared/typegen_lab.py", "shared/tui_typegen.py", "tests/test_typegen_lab.py", "tests/test_tui_typegen.py"]:
    process_file(f)
