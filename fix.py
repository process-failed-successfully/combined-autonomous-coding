import re

with open('main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_line = line
    if "parser_jwt_tui = jwt_subparsers.add_parser(\"tui\", help=\"Launch JWT Lab TUI.\")" in line:
        new_line = "    jwt_subparsers.add_parser(\"tui\", help=\"Launch JWT Lab TUI.\")\n"
    elif "parser_sql_tui = sql_subparsers.add_parser(\"tui\", help=\"Launch interactive TUI for SQL Lab.\")" in line:
        new_line = "    sql_subparsers.add_parser(\"tui\", help=\"Launch interactive TUI for SQL Lab.\")\n"
    new_lines.append(new_line)

with open('main.py', 'w') as f:
    f.writelines(new_lines)
