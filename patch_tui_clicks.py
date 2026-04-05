import os
import glob
import re

tests_dir = "tests"
count = 0

for file in glob.glob(os.path.join(tests_dir, "test_*.py")):
    with open(file, 'r') as f:
        content = f.read()

    new_content = content

    # We want to replace `await pilot.click(selector)`
    # with `app.query_one(selector).press()\n{indent}await pilot.pause()`
    # but we must preserve the indentation of the line where `await pilot.click` appears.

    def repl(match):
        indent = match.group(1)
        selector = match.group(2)
        # Using .press() directly on the widget
        return f"{indent}app.query_one({selector}).press()\n{indent}await pilot.pause()"

    pattern = re.compile(r'^([ \t]*)await pilot\.click\((["\'][^"\']+["\'])\)', re.MULTILINE)

    if pattern.search(new_content):
        new_content = pattern.sub(repl, new_content)
        count += 1
        with open(file, 'w') as f:
            f.write(new_content)

print(f"Modified {count} files.")
