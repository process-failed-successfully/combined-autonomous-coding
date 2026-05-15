import sys

with open("tests/test_did_you_mean.py", "r") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    if line.startswith("def test_did_you_mean_suggestion()"):
        new_lines.append("\n")
    if line.startswith("def test_did_you_mean_no_suggestion()"):
        new_lines.append("\n")
    new_lines.append(line)

with open("tests/test_did_you_mean.py", "w") as f:
    f.writelines(new_lines)
